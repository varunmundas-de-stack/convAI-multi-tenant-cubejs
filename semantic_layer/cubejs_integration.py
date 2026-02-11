"""
Cube.js Integration for Semantic Layer
Bridges existing YAML-based semantic layer with Cube.js API
"""
import requests
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class CubeJSConfig:
    """Cube.js API configuration"""
    base_url: str = "http://localhost:4000/cubejs-api/v1"
    api_secret: str = ""


class CubeJSClient:
    """
    Client for interacting with Cube.js API
    Translates semantic layer queries to Cube.js format
    """

    def __init__(self, config: CubeJSConfig):
        self.config = config
        self.headers = {
            "Authorization": config.api_secret,
            "Content-Type": "application/json"
        }

    def execute_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Cube.js query

        Args:
            query: Cube.js query object

        Returns:
            Query results
        """
        url = f"{self.config.base_url}/load"
        params = {"query": json.dumps(query)}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def translate_semantic_query(self, semantic_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate semantic layer query to Cube.js format

        Args:
            semantic_query: Query in semantic layer format

        Returns:
            Query in Cube.js format
        """
        cube_query = {}

        # Translate metrics to measures
        if "metrics" in semantic_query:
            cube_query["measures"] = [
                self._map_metric_to_measure(m) for m in semantic_query["metrics"]
            ]

        # Translate dimensions
        if "dimensions" in semantic_query:
            cube_query["dimensions"] = [
                self._map_dimension(d) for d in semantic_query["dimensions"]
            ]

        # Translate filters
        if "filters" in semantic_query:
            cube_query["filters"] = [
                self._map_filter(f) for f in semantic_query["filters"]
            ]

        # Translate time dimensions
        if "time_dimension" in semantic_query:
            cube_query["timeDimensions"] = [{
                "dimension": self._map_dimension(semantic_query["time_dimension"]),
                "granularity": semantic_query.get("granularity", "day")
            }]

        # Limit
        if "limit" in semantic_query:
            cube_query["limit"] = semantic_query["limit"]

        return cube_query

    def _map_metric_to_measure(self, metric: str) -> str:
        """Map semantic layer metric to Cube.js measure"""
        metric_mapping = {
            "total_transactions": "Transactions.count",
            "transaction_volume": "Transactions.total_amount",
            "average_transaction_amount": "Transactions.average_amount",
            "total_deposits": "Transactions.total_amount",  # + filter
            "total_withdrawals": "Transactions.total_amount",  # + filter
            "active_customers": "Customers.active_count",
            "average_credit_score": "Customers.average_credit_score",
        }
        return metric_mapping.get(metric, f"Transactions.{metric}")

    def _map_dimension(self, dimension: str) -> str:
        """Map semantic layer dimension to Cube.js dimension"""
        dimension_mapping = {
            "date": "Dates.date",
            "year": "Dates.year",
            "quarter": "Dates.quarter",
            "month": "Dates.month",
            "month_name": "Dates.month_name",
            "customer": "Customers.name",
            "customer_segment": "Customers.customer_segment",
            "city": "Customers.city",
            "state": "Customers.state",
            "account_type": "Accounts.account_type",
            "region": "Accounts.region",
            "transaction_type": "TransactionTypes.transaction_type",
        }
        return dimension_mapping.get(dimension, dimension)

    def _map_filter(self, filter_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Map semantic layer filter to Cube.js filter"""
        dimension = self._map_dimension(filter_obj.get("dimension", ""))
        operator = filter_obj.get("operator", "equals")
        values = filter_obj.get("values", [])

        # Map operators
        operator_mapping = {
            "IN": "equals",
            "=": "equals",
            "!=": "notEquals",
            ">": "gt",
            ">=": "gte",
            "<": "lt",
            "<=": "lte",
            "LIKE": "contains",
        }

        cube_operator = operator_mapping.get(operator, "equals")

        return {
            "dimension": dimension,
            "operator": cube_operator,
            "values": values
        }


class SemanticLayerCubeJSBridge:
    """
    Bridge between existing semantic layer and Cube.js
    Provides unified interface for querying either backend
    """

    def __init__(self, use_cubejs: bool = False, cubejs_config: Optional[CubeJSConfig] = None):
        self.use_cubejs = use_cubejs
        self.cubejs_client = None

        if use_cubejs and cubejs_config:
            self.cubejs_client = CubeJSClient(cubejs_config)

    def query(self, semantic_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute query using either semantic layer or Cube.js

        Args:
            semantic_query: Query in semantic layer format

        Returns:
            Query results
        """
        if self.use_cubejs and self.cubejs_client:
            # Use Cube.js
            cube_query = self.cubejs_client.translate_semantic_query(semantic_query)
            return self.cubejs_client.execute_query(cube_query)
        else:
            # Use existing semantic layer
            from semantic_layer import SemanticLayer
            sl = SemanticLayer("semantic_layer/config.yaml")
            return sl.execute_query(semantic_query)

    def get_available_metrics(self) -> List[str]:
        """Get list of available metrics"""
        if self.use_cubejs:
            # Could fetch from Cube.js meta API
            return ["total_transactions", "transaction_volume", "average_transaction_amount"]
        else:
            from semantic_layer import SemanticLayer
            sl = SemanticLayer("semantic_layer/config.yaml")
            return list(sl.config.get("metrics", {}).keys())

    def get_available_dimensions(self) -> List[str]:
        """Get list of available dimensions"""
        if self.use_cubejs:
            return ["date", "customer", "account_type", "region"]
        else:
            from semantic_layer import SemanticLayer
            sl = SemanticLayer("semantic_layer/config.yaml")
            return list(sl.config.get("dimensions", {}).keys())
