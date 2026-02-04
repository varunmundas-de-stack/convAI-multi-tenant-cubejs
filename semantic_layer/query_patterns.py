"""
Query Pattern Grammar System
Implements finite query archetypes with pattern-specific optimizations
"""
from abc import ABC, abstractmethod
from typing import Optional
from semantic_layer.schemas import SemanticQuery, IntentType, Sorting, TimeContext
from semantic_layer.ast_builder import Query


class QueryPattern(ABC):
    """Base class for query patterns"""

    @abstractmethod
    def matches(self, semantic_query: SemanticQuery) -> bool:
        """Check if this pattern matches the query"""
        pass

    @abstractmethod
    def optimize(self, semantic_query: SemanticQuery) -> SemanticQuery:
        """Apply pattern-specific optimizations"""
        pass

    def get_description(self) -> str:
        """Get pattern description"""
        return self.__class__.__name__


class SnapshotPattern(QueryPattern):
    """
    Snapshot pattern - Single point-in-time aggregate
    Example: "Total sales this month"
    """

    def matches(self, semantic_query: SemanticQuery) -> bool:
        return semantic_query.intent == IntentType.SNAPSHOT

    def optimize(self, semantic_query: SemanticQuery) -> SemanticQuery:
        """Optimize snapshot queries"""
        # Snapshot queries are already simple - no optimization needed
        return semantic_query


class TrendPattern(QueryPattern):
    """
    Trend pattern - Time-series over multiple periods
    Example: "Sales by week for last 4 weeks"

    Optimizations:
    - Ensure time dimension in group_by
    - Force ascending time sort for chronological display
    - Add time grain validation
    """

    def matches(self, semantic_query: SemanticQuery) -> bool:
        return semantic_query.intent == IntentType.TREND

    def optimize(self, semantic_query: SemanticQuery) -> SemanticQuery:
        """Optimize trend queries"""
        from copy import deepcopy
        optimized = deepcopy(semantic_query)

        # Ensure time dimension is in group_by
        time_dimensions = ['date', 'week', 'month', 'month_name', 'quarter', 'year',
                          'fiscal_week', 'fiscal_month', 'fiscal_quarter', 'fiscal_year']

        has_time_dim = any(dim in optimized.dimensionality.group_by
                          for dim in time_dimensions)

        if not has_time_dim:
            # Add appropriate time dimension based on grain
            grain = optimized.time_context.grain
            if grain == 'week':
                optimized.dimensionality.group_by.insert(0, 'week')
            elif grain == 'month':
                optimized.dimensionality.group_by.insert(0, 'month_name')
            elif grain == 'quarter':
                optimized.dimensionality.group_by.insert(0, 'quarter')
            elif grain == 'year':
                optimized.dimensionality.group_by.insert(0, 'year')
            else:
                optimized.dimensionality.group_by.insert(0, 'date')

        # Force time-based sorting for chronological display
        if optimized.sorting:
            # Keep existing sorting but ensure it's on time dimension
            pass
        else:
            # Add default time sorting
            time_dim = next((dim for dim in optimized.dimensionality.group_by
                           if dim in time_dimensions), None)
            if time_dim:
                optimized.sorting = Sorting(
                    order_by=time_dim,
                    direction="ASC",  # Chronological
                    limit=None
                )

        return optimized


class ComparisonPattern(QueryPattern):
    """
    Comparison pattern - Period-over-period analysis
    Example: "This month vs last month", "YoY growth"

    Optimizations:
    - Set up comparison window
    - Use window functions (LAG/LEAD) when possible
    - Calculate growth/delta metrics
    """

    def matches(self, semantic_query: SemanticQuery) -> bool:
        return semantic_query.intent == IntentType.COMPARISON

    def optimize(self, semantic_query: SemanticQuery) -> SemanticQuery:
        """Optimize comparison queries"""
        from copy import deepcopy
        optimized = deepcopy(semantic_query)

        # Ensure comparison is configured
        if not optimized.comparison:
            from semantic_layer.schemas import Comparison
            # Set up default comparison based on time window
            window = optimized.time_context.window
            if 'month' in window.lower():
                baseline = 'last_month'
            elif 'quarter' in window.lower():
                baseline = 'last_quarter'
            elif 'year' in window.lower():
                baseline = 'last_year'
            else:
                baseline = 'previous_period'

            optimized.comparison = Comparison(
                type="period",
                baseline=baseline,
                metric_variant="growth"
            )

        # Set metric variant to growth for comparisons
        if optimized.metric_request.metric_variant == "absolute":
            optimized.metric_request.metric_variant = "growth"

        return optimized


class RankingPattern(QueryPattern):
    """
    Ranking pattern - Top N / Bottom N queries
    Example: "Top 10 brands by sales"

    Optimizations:
    - Ensure sorting is set
    - Ensure limit is reasonable
    - Optimize for large result sets
    """

    def matches(self, semantic_query: SemanticQuery) -> bool:
        return semantic_query.intent == IntentType.RANKING

    def optimize(self, semantic_query: SemanticQuery) -> SemanticQuery:
        """Optimize ranking queries"""
        from copy import deepcopy
        optimized = deepcopy(semantic_query)

        # Ensure sorting exists
        if not optimized.sorting:
            optimized.sorting = Sorting(
                order_by=optimized.metric_request.primary_metric,
                direction="DESC",
                limit=10  # Default top 10
            )
        else:
            # Ensure limit is set and reasonable
            if not optimized.sorting.limit:
                optimized.sorting.limit = 10
            elif optimized.sorting.limit > 100:
                # Cap at 100 for performance
                optimized.sorting.limit = 100

        return optimized


class DiagnosticPattern(QueryPattern):
    """
    Diagnostic pattern - Root cause analysis with multi-query workflow
    Example: "Why did sales drop?"

    This pattern triggers the QueryOrchestrator to run multiple queries:
    1. Trend confirmation (validate the drop)
    2. Contribution analysis by key dimensions
    3. Anomaly detection
    4. Recommendations
    """

    def matches(self, semantic_query: SemanticQuery) -> bool:
        return semantic_query.intent == IntentType.DIAGNOSTIC

    def optimize(self, semantic_query: SemanticQuery) -> SemanticQuery:
        """Optimize diagnostic queries"""
        from copy import deepcopy
        optimized = deepcopy(semantic_query)

        # Ensure diagnostics is enabled
        if not optimized.diagnostics:
            from semantic_layer.schemas import Diagnostics
            optimized.diagnostics = Diagnostics(
                enabled=True,
                diagnostic_type="contribution",
                dimensions=['brand_name', 'state_name', 'channel_name'],  # Default dimensions
                threshold=0.05
            )
        else:
            optimized.diagnostics.enabled = True
            # Ensure we have dimensions to analyze
            if not optimized.diagnostics.dimensions:
                optimized.diagnostics.dimensions = ['brand_name', 'state_name', 'channel_name']

        return optimized


class PatternRegistry:
    """
    Registry of query patterns with pattern matching and routing
    """

    def __init__(self):
        self.patterns = [
            TrendPattern(),
            ComparisonPattern(),
            RankingPattern(),
            DiagnosticPattern(),
            SnapshotPattern(),  # Default/fallback pattern
        ]

    def get_pattern(self, semantic_query: SemanticQuery) -> QueryPattern:
        """
        Find matching pattern for query.

        Args:
            semantic_query: Query to match

        Returns:
            Matching QueryPattern (defaults to SnapshotPattern if no match)
        """
        for pattern in self.patterns:
            if pattern.matches(semantic_query):
                return pattern

        # Default to snapshot
        return SnapshotPattern()

    def optimize_query(self, semantic_query: SemanticQuery) -> SemanticQuery:
        """
        Apply pattern-specific optimizations to query.

        Args:
            semantic_query: Query to optimize

        Returns:
            Optimized SemanticQuery
        """
        pattern = self.get_pattern(semantic_query)
        optimized = pattern.optimize(semantic_query)
        return optimized

    def get_pattern_name(self, semantic_query: SemanticQuery) -> str:
        """Get the name of the matching pattern"""
        pattern = self.get_pattern(semantic_query)
        return pattern.get_description()


# Convenience function
def optimize_with_pattern(semantic_query: SemanticQuery) -> SemanticQuery:
    """
    Convenience function to optimize query with pattern matching.

    Args:
        semantic_query: Query to optimize

    Returns:
        Optimized query with pattern-specific optimizations applied
    """
    registry = PatternRegistry()
    return registry.optimize_query(semantic_query)
