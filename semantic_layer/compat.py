"""
Backward compatibility adapter between legacy QueryIntent and new SemanticQuery.
Allows gradual migration without breaking existing code.
"""
from semantic_layer.models import QueryIntent as LegacyIntent
from semantic_layer.schemas import (
    SemanticQuery,
    MetricRequest,
    Dimensionality,
    TimeContext,
    Filter,
    Sorting,
    IntentType
)
from typing import List


class IntentAdapter:
    """Adapter to convert between old and new intent formats"""

    @staticmethod
    def upgrade(legacy: LegacyIntent) -> SemanticQuery:
        """
        Convert legacy QueryIntent to new SemanticQuery format.

        Args:
            legacy: Legacy QueryIntent object

        Returns:
            SemanticQuery: New structured query format
        """
        # Map legacy intent types to new IntentType enum
        intent_mapping = {
            "aggregate": IntentType.SNAPSHOT,
            "trend": IntentType.TREND,
            "comparison": IntentType.COMPARISON,
            "ranking": IntentType.RANKING,
            "diagnostic": IntentType.DIAGNOSTIC,
        }

        intent = intent_mapping.get(
            legacy.intent_type.lower(),
            IntentType.SNAPSHOT
        )

        # Create metric request
        metric_request = MetricRequest(
            primary_metric=legacy.metrics[0] if legacy.metrics else "secondary_sales_value",
            secondary_metrics=legacy.metrics[1:] if len(legacy.metrics) > 1 else [],
            metric_variant="absolute"
        )

        # Create dimensionality
        dimensionality = Dimensionality(
            group_by=legacy.group_by or legacy.dimensions,
            hierarchy_level={}
        )

        # Create time context
        time_context = TimeContext(
            window=legacy.time_period or "last_4_weeks",
            grain="day"
        )

        # Convert legacy filters (basic string filters) to structured filters
        filters: List[Filter] = []
        # Legacy filters are simple strings like "state = 'Tamil Nadu'"
        # For now, we'll skip detailed parsing but keep the structure ready

        # Create sorting if provided
        sorting = None
        if legacy.sorting:
            sorting = Sorting(
                order_by=legacy.sorting.get("field", legacy.metrics[0] if legacy.metrics else "value"),
                direction=legacy.sorting.get("direction", "DESC"),
                limit=legacy.limit
            )
        elif legacy.limit:
            sorting = Sorting(
                order_by=legacy.metrics[0] if legacy.metrics else "value",
                direction="DESC",
                limit=legacy.limit
            )

        # Build SemanticQuery
        semantic_query = SemanticQuery(
            intent=intent,
            metric_request=metric_request,
            dimensionality=dimensionality,
            time_context=time_context,
            filters=filters,
            sorting=sorting,
            confidence=legacy.confidence_score,
            original_question=legacy.original_question
        )

        return semantic_query

    @staticmethod
    def downgrade(semantic: SemanticQuery) -> LegacyIntent:
        """
        Convert new SemanticQuery back to legacy QueryIntent format.
        Used for gradual rollback if needed.

        Args:
            semantic: New SemanticQuery object

        Returns:
            QueryIntent: Legacy query intent format
        """
        # Build metrics list
        metrics = [semantic.metric_request.primary_metric]
        metrics.extend(semantic.metric_request.secondary_metrics)

        # Map intent back
        intent_reverse_mapping = {
            IntentType.SNAPSHOT: "aggregate",
            IntentType.TREND: "trend",
            IntentType.COMPARISON: "comparison",
            IntentType.RANKING: "ranking",
            IntentType.DIAGNOSTIC: "diagnostic"
        }

        # Build sorting dict
        sorting = None
        limit = None
        if semantic.sorting:
            sorting = {
                "field": semantic.sorting.order_by,
                "direction": semantic.sorting.direction
            }
            limit = semantic.sorting.limit

        legacy = LegacyIntent(
            intent_type=intent_reverse_mapping.get(semantic.intent, "aggregate"),
            metrics=metrics,
            dimensions=semantic.dimensionality.group_by,
            group_by=semantic.dimensionality.group_by,
            filters=[],  # Simplified for now
            time_period=semantic.time_context.window,
            sorting=sorting,
            limit=limit,
            original_question=semantic.original_question,
            confidence_score=semantic.confidence
        )

        return legacy


# Convenience functions
def legacy_to_semantic(legacy_intent: LegacyIntent) -> SemanticQuery:
    """Convert legacy intent to semantic query"""
    return IntentAdapter.upgrade(legacy_intent)


def semantic_to_legacy(semantic_query: SemanticQuery) -> LegacyIntent:
    """Convert semantic query to legacy intent"""
    return IntentAdapter.downgrade(semantic_query)
