"""
Query Executor - Executes SQL queries against DuckDB
"""
import duckdb
import threading
import time
import decimal
from typing import List, Dict, Any
from pathlib import Path
from semantic_layer.models import QueryResult


class QueryExecutor:
    """Execute SQL queries and return results"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._local = threading.local()  # one connection per thread — thread-safe

    def _get_conn(self):
        """Return (or lazily open) the per-thread DuckDB connection."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        conn = getattr(self._local, 'conn', None)
        if conn is None:
            conn = duckdb.connect(str(self.db_path), read_only=True)
            self._local.conn = conn
        return conn

    # ── kept for backward-compat (context-manager usage) ──────────────────
    def connect(self):
        self._get_conn()

    def disconnect(self):
        conn = getattr(self._local, 'conn', None)
        if conn:
            conn.close()
            self._local.conn = None

    def execute(self, sql: str) -> QueryResult:
        """
        Execute SQL query and return results
        """
        start_time = time.time()

        try:
            result = self._get_conn().execute(sql)

            # Fetch all results
            rows = result.fetchall()
            columns = [desc[0] for desc in result.description]

            # Convert to list of dicts, normalizing non-JSON-safe types
            data = []
            for row in rows:
                row_dict = {}
                for col, val in zip(columns, row):
                    if isinstance(val, decimal.Decimal):
                        val = float(val)
                    row_dict[col] = val
                data.append(row_dict)

            execution_time = (time.time() - start_time) * 1000  # ms

            return QueryResult(
                data=data,
                columns=columns,
                row_count=len(data),
                sql_query=sql,
                execution_time_ms=round(execution_time, 2)
            )

        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}\nSQL: {sql}")

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a table"""
        if not self.conn:
            self.connect()

        # Get row count
        count_result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        row_count = count_result[0] if count_result else 0

        # Get column info
        columns_result = self.conn.execute(f"DESCRIBE {table_name}").fetchall()
        columns = [
            {
                'name': col[0],
                'type': col[1],
                'null': col[2]
            }
            for col in columns_result
        ]

        return {
            'table_name': table_name,
            'row_count': row_count,
            'columns': columns
        }

    def list_tables(self) -> List[str]:
        """List all tables in the database"""
        if not self.conn:
            self.connect()

        result = self.conn.execute("SHOW TABLES").fetchall()
        return [row[0] for row in result]

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
