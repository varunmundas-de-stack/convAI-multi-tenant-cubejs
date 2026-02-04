"""
Audit logging for query execution tracking
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class AuditLogger:
    """Logs all query executions for audit trail"""

    def __init__(self, log_path: str = "logs/audit.jsonl"):
        """
        Initialize audit logger.

        Args:
            log_path: Path to audit log file (JSON Lines format)
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_query(
        self,
        query_id: str,
        user_id: str,
        semantic_query: Dict[str, Any],
        sql: str,
        result_count: int,
        exec_time: float,
        success: bool = True,
        error: str = None
    ):
        """
        Log query execution.

        Args:
            query_id: Unique query ID
            user_id: User who executed query
            semantic_query: Semantic query dict
            sql: Generated SQL
            result_count: Number of rows returned
            exec_time: Execution time in milliseconds
            success: Whether query succeeded
            error: Error message if failed
        """
        record = {
            'timestamp': datetime.utcnow().isoformat(),
            'query_id': query_id,
            'user_id': user_id,
            'question': semantic_query.get('original_question', ''),
            'intent': semantic_query.get('intent', 'unknown'),
            'metric': semantic_query.get('metric_request', {}).get('primary_metric', ''),
            'dimensions': semantic_query.get('dimensionality', {}).get('group_by', []),
            'time_window': semantic_query.get('time_context', {}).get('window', ''),
            'filters': len(semantic_query.get('filters', [])),
            'sql': sql,
            'result_count': result_count,
            'execution_time_ms': exec_time,
            'success': success,
            'error': error
        }

        # Append to log file (JSON Lines format)
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record) + '\n')

    def get_recent_queries(self, limit: int = 100) -> list:
        """
        Get recent queries from audit log.

        Args:
            limit: Max number of queries to return

        Returns:
            List of recent query records
        """
        if not self.log_path.exists():
            return []

        queries = []
        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    queries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        # Return most recent first
        return queries[-limit:][::-1]

    def get_user_query_history(self, user_id: str, limit: int = 50) -> list:
        """
        Get query history for specific user.

        Args:
            user_id: User ID
            limit: Max queries to return

        Returns:
            List of user's queries
        """
        recent = self.get_recent_queries(limit=1000)
        user_queries = [q for q in recent if q.get('user_id') == user_id]
        return user_queries[:limit]

    def get_query_stats(self) -> Dict[str, Any]:
        """
        Get aggregate statistics from audit log.

        Returns:
            Dict with query statistics
        """
        queries = self.get_recent_queries(limit=10000)

        if not queries:
            return {
                'total_queries': 0,
                'successful_queries': 0,
                'failed_queries': 0,
                'avg_execution_time_ms': 0,
                'unique_users': 0
            }

        successful = [q for q in queries if q.get('success', False)]
        failed = [q for q in queries if not q.get('success', False)]
        exec_times = [q.get('execution_time_ms', 0) for q in successful]
        users = set(q.get('user_id') for q in queries)

        return {
            'total_queries': len(queries),
            'successful_queries': len(successful),
            'failed_queries': len(failed),
            'avg_execution_time_ms': sum(exec_times) / len(exec_times) if exec_times else 0,
            'unique_users': len(users),
            'most_common_metrics': self._most_common([q.get('metric', '') for q in queries], 5)
        }

    @staticmethod
    def _most_common(items: list, n: int) -> list:
        """Get n most common items"""
        from collections import Counter
        return [item for item, count in Counter(items).most_common(n)]
