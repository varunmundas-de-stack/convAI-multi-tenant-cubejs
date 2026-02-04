"""
Query Orchestrator for Multi-Query Diagnostic Workflows
Handles complex diagnostic queries that require multiple SQL queries
"""
from typing import Dict, Any, List
from semantic_layer.schemas import SemanticQuery, IntentType, MetricRequest, Dimensionality, Sorting
from semantic_layer.semantic_layer import SemanticLayer
from semantic_layer.query_builder import ASTQueryBuilder
from copy import deepcopy
import time


class QueryOrchestrator:
    """
    Orchestrates multi-query workflows, particularly for diagnostic analysis.

    Handles:
    - Single query execution
    - Multi-query diagnostic workflows
    - Result synthesis and analysis
    - Recommendation generation
    """

    def __init__(self, semantic_layer: SemanticLayer, query_executor):
        """
        Initialize orchestrator.

        Args:
            semantic_layer: SemanticLayer instance
            query_executor: QueryExecutor instance for running SQL
        """
        self.semantic_layer = semantic_layer
        self.executor = query_executor
        self.builder = ASTQueryBuilder(semantic_layer)

    def execute(self, semantic_query: SemanticQuery) -> Dict[str, Any]:
        """
        Execute query - routes to appropriate execution strategy.

        Args:
            semantic_query: Query to execute

        Returns:
            Dict with results and metadata
        """
        if semantic_query.intent == IntentType.DIAGNOSTIC:
            return self._execute_diagnostic(semantic_query)
        else:
            return self._execute_single(semantic_query)

    def _execute_single(self, semantic_query: SemanticQuery) -> Dict[str, Any]:
        """
        Execute single query.

        Args:
            semantic_query: Query to execute

        Returns:
            Dict with query results
        """
        # Build AST
        query_ast = self.builder.build_query(semantic_query)

        # Generate SQL
        sql = query_ast.to_sql()

        # Execute
        start_time = time.time()
        result = self.executor.execute(sql)
        exec_time = (time.time() - start_time) * 1000

        return {
            'query_type': 'single',
            'sql': sql,
            'results': result.data if hasattr(result, 'data') else [],
            'metadata': {
                'row_count': len(result.data) if hasattr(result, 'data') and result.data else 0,
                'execution_time_ms': exec_time,
                'intent': semantic_query.intent.value
            }
        }

    def _execute_diagnostic(self, semantic_query: SemanticQuery) -> Dict[str, Any]:
        """
        Execute multi-query diagnostic workflow.

        Workflow:
        1. Trend confirmation - Validate that metric actually changed
        2. Contribution by dimension - Find which segments drove the change
        3. Analysis synthesis - Combine insights
        4. Recommendations - Generate actionable recommendations

        Args:
            semantic_query: Diagnostic query

        Returns:
            Dict with diagnostic results and analysis
        """
        queries = []
        results = {}

        # Query 1: Trend Confirmation
        # Shows metric over time to confirm trend direction
        trend_query = deepcopy(semantic_query)
        trend_query.intent = IntentType.TREND
        trend_query.dimensionality.group_by = [self._get_time_dimension(semantic_query)]
        trend_query.sorting = Sorting(
            order_by=self._get_time_dimension(semantic_query),
            direction="ASC",
            limit=None
        )
        queries.append(('trend_confirmation', trend_query))

        # Query 2-N: Contribution Analysis
        # Show top contributors by each key dimension
        dimensions_to_analyze = self._get_diagnostic_dimensions(semantic_query)

        for dim in dimensions_to_analyze:
            contrib_query = deepcopy(semantic_query)
            contrib_query.intent = IntentType.RANKING
            contrib_query.dimensionality.group_by = [dim]
            contrib_query.sorting = Sorting(
                order_by=semantic_query.metric_request.primary_metric,
                direction="DESC",
                limit=10
            )
            queries.append((f'contribution_{dim}', contrib_query))

        # Execute all queries
        total_exec_time = 0
        for name, query in queries:
            query_result = self._execute_single(query)
            results[name] = query_result
            total_exec_time += query_result['metadata']['execution_time_ms']

        # Analyze and synthesize
        analysis = self._analyze_diagnostic(results, semantic_query)

        return {
            'query_type': 'diagnostic',
            'sub_queries': results,
            'analysis': analysis,
            'metadata': {
                'total_queries': len(queries),
                'total_execution_time_ms': total_exec_time,
                'intent': 'diagnostic'
            }
        }

    def _get_time_dimension(self, semantic_query: SemanticQuery) -> str:
        """Get appropriate time dimension based on query grain"""
        grain = semantic_query.time_context.grain
        grain_to_dimension = {
            'day': 'date',
            'week': 'week',
            'month': 'month_name',
            'quarter': 'quarter',
            'year': 'year'
        }
        return grain_to_dimension.get(grain, 'week')

    def _get_diagnostic_dimensions(self, semantic_query: SemanticQuery) -> List[str]:
        """
        Get dimensions to analyze for diagnostics.

        Priority:
        1. Dimensions specified in diagnostics.dimensions
        2. Default CPG dimensions (brand, state, channel)
        """
        if semantic_query.diagnostics and semantic_query.diagnostics.dimensions:
            return semantic_query.diagnostics.dimensions

        # Default diagnostic dimensions for CPG
        return ['brand_name', 'state_name', 'channel_name']

    def _analyze_diagnostic(
        self,
        results: Dict[str, Any],
        semantic_query: SemanticQuery
    ) -> Dict[str, Any]:
        """
        Synthesize diagnostic analysis from multiple query results.

        Args:
            results: Results from all diagnostic queries
            semantic_query: Original diagnostic query

        Returns:
            Dict with analysis findings and recommendations
        """
        metric_name = semantic_query.metric_request.primary_metric

        # Analyze trend
        trend_data = results.get('trend_confirmation', {}).get('results', [])
        trend_analysis = self._analyze_trend(trend_data, metric_name)

        # Analyze contributions
        contribution_analysis = []
        for key, value in results.items():
            if key.startswith('contribution_'):
                dim = key.replace('contribution_', '')
                contrib_data = value.get('results', [])
                if contrib_data:
                    contribution_analysis.append({
                        'dimension': dim,
                        'top_contributor': contrib_data[0],
                        'total_contributors': len(contrib_data),
                        'top_5': contrib_data[:5]
                    })

        # Generate insights
        insights = self._generate_insights(trend_analysis, contribution_analysis, metric_name)

        # Generate recommendations
        recommendations = self._generate_recommendations(trend_analysis, contribution_analysis)

        return {
            'trend_analysis': trend_analysis,
            'contribution_analysis': contribution_analysis,
            'insights': insights,
            'recommendations': recommendations
        }

    def _analyze_trend(self, trend_data: List[Dict], metric_name: str) -> Dict[str, Any]:
        """Analyze trend data to detect patterns"""
        if not trend_data or len(trend_data) < 2:
            return {
                'direction': 'insufficient_data',
                'change_pct': 0,
                'data_points': len(trend_data)
            }

        # Get first and last values
        first_value = float(trend_data[0].get(metric_name, 0))
        last_value = float(trend_data[-1].get(metric_name, 0))

        # Calculate change
        if first_value == 0:
            change_pct = 0
        else:
            change_pct = ((last_value - first_value) / first_value) * 100

        # Determine direction
        if abs(change_pct) < 1:
            direction = 'stable'
        elif change_pct > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'

        # Find peak and trough
        values = [float(d.get(metric_name, 0)) for d in trend_data]
        peak_idx = values.index(max(values))
        trough_idx = values.index(min(values))

        return {
            'direction': direction,
            'change_pct': round(change_pct, 2),
            'first_value': first_value,
            'last_value': last_value,
            'peak': {
                'value': values[peak_idx],
                'period': trend_data[peak_idx]
            },
            'trough': {
                'value': values[trough_idx],
                'period': trend_data[trough_idx]
            },
            'data_points': len(trend_data)
        }

    def _generate_insights(
        self,
        trend_analysis: Dict,
        contribution_analysis: List[Dict],
        metric_name: str
    ) -> List[str]:
        """Generate natural language insights from analysis"""
        insights = []

        # Trend insight
        direction = trend_analysis.get('direction', 'unknown')
        change_pct = trend_analysis.get('change_pct', 0)

        if direction == 'increasing':
            insights.append(
                f"[+] {metric_name} increased by {abs(change_pct):.1f}% over the period"
            )
        elif direction == 'decreasing':
            insights.append(
                f"[!] {metric_name} decreased by {abs(change_pct):.1f}% over the period"
            )
        else:
            insights.append(f"[=] {metric_name} remained stable (change: {change_pct:.1f}%)")

        # Contribution insights
        for contrib in contribution_analysis[:3]:  # Top 3 dimensions
            dim = contrib['dimension']
            top = contrib['top_contributor']
            dim_value = list(top.values())[0]  # First value is the dimension value
            metric_value = top.get(metric_name, 0)

            insights.append(
                f"[>] Top contributor in {dim}: {dim_value} (value: {metric_value:,.0f})"
            )

        return insights

    def _generate_recommendations(
        self,
        trend_analysis: Dict,
        contribution_analysis: List[Dict]
    ) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []

        direction = trend_analysis.get('direction', 'unknown')
        change_pct = abs(trend_analysis.get('change_pct', 0))

        if direction == 'decreasing' and change_pct > 5:
            recommendations.append(
                "[>] Immediate action recommended: Metric declining significantly"
            )
            recommendations.append(
                "[>] Investigate top contributing segments for root cause"
            )
            recommendations.append(
                "[>] Consider targeted interventions in high-impact areas"
            )
        elif direction == 'increasing' and change_pct > 10:
            recommendations.append(
                "[>] Positive trend: Consider scaling successful strategies"
            )
            recommendations.append(
                "[>] Analyze top performers to replicate success factors"
            )
        else:
            recommendations.append(
                "[>] Monitor trend for significant changes"
            )

        # Dimension-specific recommendations
        if contribution_analysis:
            top_dim = contribution_analysis[0]
            recommendations.append(
                f"[>] Focus analysis on {top_dim['dimension']} - shows highest variation"
            )

        return recommendations


# Convenience function
def execute_with_orchestrator(
    semantic_query: SemanticQuery,
    semantic_layer: SemanticLayer,
    query_executor
) -> Dict[str, Any]:
    """
    Convenience function to execute query with orchestrator.

    Args:
        semantic_query: Query to execute
        semantic_layer: SemanticLayer instance
        query_executor: QueryExecutor instance

    Returns:
        Execution results with analysis (if diagnostic)
    """
    orchestrator = QueryOrchestrator(semantic_layer, query_executor)
    return orchestrator.execute(semantic_query)
