"""
Observability & Metrics Tracking
Tracks usage, performance, and costs by customer and department
"""
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import sqlite3


@dataclass
class QueryMetrics:
    """Metrics for a single query"""
    query_id: str
    tenant_id: str
    department: str
    user_id: str
    question: str
    query_type: str  # 'nlq', 'sql', 'cube_api'
    execution_time_ms: float
    tokens_used: int
    llm_provider: str
    llm_model: str
    cost_usd: float
    success: bool
    error_message: Optional[str]
    timestamp: datetime


class MetricsTracker:
    """
    Tracks and stores observability metrics
    """

    def __init__(self, db_path: str = "database/observability.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize observability database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Query metrics table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_metrics (
            query_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            department TEXT,
            user_id TEXT NOT NULL,
            question TEXT,
            query_type TEXT,
            execution_time_ms REAL,
            tokens_used INTEGER,
            llm_provider TEXT,
            llm_model TEXT,
            cost_usd REAL,
            success INTEGER,
            error_message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenant_timestamp ON query_metrics(tenant_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_department ON query_metrics(department)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user ON query_metrics(user_id)")

        # Aggregated metrics table (for faster dashboards)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics_daily_agg (
            agg_date DATE,
            tenant_id TEXT,
            department TEXT,
            total_queries INTEGER,
            successful_queries INTEGER,
            failed_queries INTEGER,
            total_tokens INTEGER,
            total_cost_usd REAL,
            avg_execution_time_ms REAL,
            PRIMARY KEY (agg_date, tenant_id, department)
        )
        """)

        conn.commit()
        conn.close()

    def track_query(self, metrics: QueryMetrics):
        """Track a single query"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO query_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.query_id,
            metrics.tenant_id,
            metrics.department,
            metrics.user_id,
            metrics.question,
            metrics.query_type,
            metrics.execution_time_ms,
            metrics.tokens_used,
            metrics.llm_provider,
            metrics.llm_model,
            metrics.cost_usd,
            1 if metrics.success else 0,
            metrics.error_message,
            metrics.timestamp.isoformat()
        ))

        conn.commit()
        conn.close()

    def get_tenant_metrics(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get aggregated metrics for a tenant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            COUNT(*) as total_queries,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_queries,
            SUM(tokens_used) as total_tokens,
            SUM(cost_usd) as total_cost,
            AVG(execution_time_ms) as avg_execution_time
        FROM query_metrics
        WHERE tenant_id = ?
          AND timestamp >= datetime('now', ? || ' days')
        """, (tenant_id, -days))

        result = cursor.fetchone()
        conn.close()

        return {
            'total_queries': result[0] or 0,
            'successful_queries': result[1] or 0,
            'total_tokens': result[2] or 0,
            'total_cost_usd': round(result[3] or 0, 4),
            'avg_execution_time_ms': round(result[4] or 0, 2)
        }

    def get_department_metrics(self, tenant_id: str, department: str, days: int = 30) -> Dict[str, Any]:
        """Get metrics for a specific department"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            COUNT(*) as total_queries,
            SUM(tokens_used) as total_tokens,
            SUM(cost_usd) as total_cost,
            COUNT(DISTINCT user_id) as unique_users
        FROM query_metrics
        WHERE tenant_id = ?
          AND department = ?
          AND timestamp >= datetime('now', ? || ' days')
        """, (tenant_id, department, -days))

        result = cursor.fetchone()
        conn.close()

        return {
            'total_queries': result[0] or 0,
            'total_tokens': result[1] or 0,
            'total_cost_usd': round(result[2] or 0, 4),
            'unique_users': result[3] or 0
        }

    def get_top_questions(self, tenant_id: str, limit: int = 10) -> list:
        """Get most frequently asked questions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT question, COUNT(*) as count
        FROM query_metrics
        WHERE tenant_id = ?
          AND timestamp >= datetime('now', '-30 days')
        GROUP BY question
        ORDER BY count DESC
        LIMIT ?
        """, (tenant_id, limit))

        results = cursor.fetchall()
        conn.close()

        return [{'question': r[0], 'count': r[1]} for r in results]

    def aggregate_daily_metrics(self, date: str = None):
        """Aggregate metrics by day for faster dashboard queries"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR REPLACE INTO metrics_daily_agg
        SELECT
            DATE(timestamp) as agg_date,
            tenant_id,
            department,
            COUNT(*) as total_queries,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_queries,
            SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_queries,
            SUM(tokens_used) as total_tokens,
            SUM(cost_usd) as total_cost_usd,
            AVG(execution_time_ms) as avg_execution_time_ms
        FROM query_metrics
        WHERE DATE(timestamp) = ?
        GROUP BY DATE(timestamp), tenant_id, department
        """, (date,))

        conn.commit()
        conn.close()


class CostCalculator:
    """Calculate LLM costs based on tokens and provider"""

    # Pricing per 1K tokens (as of 2026)
    PRICING = {
        'openai': {
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002}
        },
        'anthropic': {
            'claude-3-opus': {'input': 0.015, 'output': 0.075},
            'claude-3-sonnet': {'input': 0.003, 'output': 0.015}
        },
        'azure_openai': {
            'gpt-4': {'input': 0.03, 'output': 0.06}
        }
    }

    @staticmethod
    def calculate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD"""
        pricing = CostCalculator.PRICING.get(provider, {}).get(model)
        if not pricing:
            return 0.0

        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']

        return input_cost + output_cost


# Context manager for automatic tracking
class TrackedQuery:
    """Context manager to automatically track query metrics"""

    def __init__(self, tracker: MetricsTracker, tenant_id: str, user_id: str,
                 department: str, question: str, query_type: str = 'nlq'):
        self.tracker = tracker
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.department = department
        self.question = question
        self.query_type = query_type
        self.start_time = None
        self.query_id = f"{tenant_id}_{int(time.time() * 1000)}"

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = (time.time() - self.start_time) * 1000  # ms

        metrics = QueryMetrics(
            query_id=self.query_id,
            tenant_id=self.tenant_id,
            department=self.department,
            user_id=self.user_id,
            question=self.question,
            query_type=self.query_type,
            execution_time_ms=execution_time,
            tokens_used=0,  # Set externally
            llm_provider='',
            llm_model='',
            cost_usd=0.0,
            success=exc_type is None,
            error_message=str(exc_val) if exc_val else None,
            timestamp=datetime.now()
        )

        self.tracker.track_query(metrics)
        return False  # Don't suppress exceptions
