"""
Enhanced semantic query schemas for production-grade conversational AI system.
Replaces basic QueryIntent with structured SemanticQuery.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from enum import Enum


class IntentType(str, Enum):
    """Query intent types"""
    TREND = "trend"
    COMPARISON = "comparison"
    RANKING = "ranking"
    DIAGNOSTIC = "diagnostic"
    SNAPSHOT = "snapshot"


class MetricRequest(BaseModel):
    """Metric configuration for the query"""
    primary_metric: str = Field(..., description="Primary metric to compute")
    secondary_metrics: List[str] = Field(default_factory=list, description="Additional metrics")
    metric_variant: Literal["absolute", "growth", "delta", "contribution"] = Field(
        default="absolute",
        description="Type of metric calculation"
    )


class Dimensionality(BaseModel):
    """Dimension configuration for grouping and slicing"""
    group_by: List[str] = Field(default_factory=list, description="Dimensions to group by")
    hierarchy_level: Dict[str, str] = Field(
        default_factory=dict,
        description="Dimension hierarchy level (e.g., product: brand_name)"
    )


class TimeContext(BaseModel):
    """Time window and granularity configuration"""
    time_dimension: str = Field(default="invoice_date", description="Time dimension field")
    window: str = Field(default="last_4_weeks", description="Time window (e.g., last_4_weeks, mtd, ytd)")
    grain: str = Field(default="day", description="Time granularity (day, week, month)")
    comparison_window: Optional[str] = Field(None, description="Comparison period for trend analysis")


class Filter(BaseModel):
    """Filter condition"""
    dimension: str = Field(..., description="Dimension to filter")
    operator: Literal["=", "IN", "NOT IN", "BETWEEN", ">", "<", ">=", "<="] = Field(
        ...,
        description="Filter operator"
    )
    values: List[Any] = Field(..., description="Filter values")


class Comparison(BaseModel):
    """Comparison configuration for period-over-period analysis"""
    type: Literal["period", "peer", "rank"] = Field(..., description="Comparison type")
    baseline: str = Field(..., description="Baseline for comparison (e.g., last_month, last_year)")
    metric_variant: str = Field(default="growth", description="How to show comparison (growth, delta)")


class Diagnostics(BaseModel):
    """Diagnostic analysis configuration"""
    enabled: bool = Field(default=False, description="Enable diagnostic workflow")
    diagnostic_type: Literal["contribution", "driver_analysis", "mix_shift"] = Field(
        default="contribution",
        description="Type of diagnostic analysis"
    )
    dimensions: List[str] = Field(
        default_factory=list,
        description="Dimensions to analyze for contribution"
    )
    threshold: float = Field(default=0.05, description="Significance threshold (5%)")


class Sorting(BaseModel):
    """Sorting and limiting configuration"""
    order_by: str = Field(..., description="Field to sort by")
    direction: Literal["ASC", "DESC"] = Field(default="DESC", description="Sort direction")
    limit: Optional[int] = Field(None, description="Maximum number of results")


class ResultShape(BaseModel):
    """Output format configuration"""
    format: Literal["table", "pivot", "chart"] = Field(default="table", description="Result format")
    chart_type: Optional[Literal["line", "bar", "stacked_bar", "heatmap"]] = Field(
        None,
        description="Chart type if format=chart"
    )


class SemanticQuery(BaseModel):
    """
    Production-grade semantic query schema.
    Replaces QueryIntent with comprehensive structured representation.
    """
    schema_version: str = Field(default="1.0", description="Schema version")
    intent: IntentType = Field(..., description="Query intent type")
    metric_request: MetricRequest = Field(..., description="Metric configuration")
    dimensionality: Dimensionality = Field(
        default_factory=Dimensionality,
        description="Dimension configuration"
    )
    time_context: TimeContext = Field(
        default_factory=TimeContext,
        description="Time window configuration"
    )
    filters: List[Filter] = Field(default_factory=list, description="Filter conditions")
    comparison: Optional[Comparison] = Field(None, description="Comparison configuration")
    diagnostics: Optional[Diagnostics] = Field(None, description="Diagnostic configuration")
    sorting: Optional[Sorting] = Field(None, description="Sorting configuration")
    result_shape: ResultShape = Field(default_factory=ResultShape, description="Output format")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="LLM confidence score")
    original_question: str = Field(..., description="Original user question")

    class Config:
        json_schema_extra = {
            "example": {
                "schema_version": "1.0",
                "intent": "trend",
                "metric_request": {
                    "primary_metric": "secondary_sales_value",
                    "metric_variant": "absolute"
                },
                "dimensionality": {
                    "group_by": ["week", "brand_name"]
                },
                "time_context": {
                    "window": "last_4_weeks",
                    "grain": "week"
                },
                "filters": [
                    {
                        "dimension": "state_name",
                        "operator": "=",
                        "values": ["Tamil Nadu"]
                    }
                ],
                "sorting": {
                    "order_by": "week",
                    "direction": "ASC"
                },
                "result_shape": {
                    "format": "chart",
                    "chart_type": "line"
                },
                "confidence": 0.95,
                "original_question": "Show sales trend by week for last 4 weeks in Tamil Nadu"
            }
        }


# Legacy support - keep for backward compatibility
class QueryIntent(BaseModel):
    """
    DEPRECATED: Legacy QueryIntent schema.
    Use SemanticQuery instead. Maintained for backward compatibility.
    """
    intent_type: str
    metrics: List[str]
    dimensions: List[str] = []
    group_by: List[str] = []
    filters: List[str] = []
    time_period: Optional[str] = None
    sorting: Optional[Dict[str, str]] = None
    limit: Optional[int] = None
    original_question: str
    confidence_score: float = 0.0

    class Config:
        json_schema_extra = {
            "deprecated": True,
            "replacement": "SemanticQuery"
        }
