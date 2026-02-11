"""
Multi-Database Manager
Handles connections to different database engines per tenant
"""
import yaml
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import duckdb


@dataclass
class DatabaseConnection:
    """Database connection configuration"""
    tenant_id: str
    tenant_name: str
    db_type: str
    connection_params: Dict[str, Any]
    features: Dict[str, bool]


class MultiDatabaseManager:
    """
    Manager for multiple database connections
    Supports DuckDB, PostgreSQL, and MS SQL Server
    """

    def __init__(self, config_path: str = "config/database_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.connections = {}

    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration from YAML"""
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Replace environment variables
        return self._replace_env_vars(config)

    def _replace_env_vars(self, obj: Any) -> Any:
        """Recursively replace ${VAR:default} with environment variables"""
        if isinstance(obj, dict):
            return {k: self._replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            # Parse ${VAR:default}
            var_spec = obj[2:-1]
            if ":" in var_spec:
                var_name, default = var_spec.split(":", 1)
                return os.getenv(var_name, default)
            else:
                return os.getenv(var_spec, "")
        return obj

    def get_connection(self, tenant_id: str):
        """
        Get database connection for tenant

        Args:
            tenant_id: Tenant identifier

        Returns:
            Database connection object
        """
        if tenant_id in self.connections:
            return self.connections[tenant_id]

        tenant_config = self.config['tenants'].get(tenant_id)
        if not tenant_config:
            raise ValueError(f"Tenant {tenant_id} not found in configuration")

        db_type = tenant_config['database_type']

        if db_type == 'duckdb':
            conn = self._get_duckdb_connection(tenant_config)
        elif db_type == 'postgresql':
            conn = self._get_postgresql_connection(tenant_config)
        elif db_type == 'mssql':
            conn = self._get_mssql_connection(tenant_config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        self.connections[tenant_id] = conn
        return conn

    def _get_duckdb_connection(self, config: Dict[str, Any]):
        """Get DuckDB connection"""
        path = config['connection']['path']
        settings = self.config['database_settings']['duckdb']

        conn = duckdb.connect(path)

        # Apply settings
        conn.execute(f"SET threads={settings['threads']}")
        conn.execute(f"SET memory_limit='{settings['memory_limit']}'")

        # Load extensions
        for ext in settings.get('extensions', []):
            try:
                conn.execute(f"INSTALL {ext}")
                conn.execute(f"LOAD {ext}")
            except Exception as e:
                print(f"Warning: Could not load extension {ext}: {e}")

        return conn

    def _get_postgresql_connection(self, config: Dict[str, Any]):
        """Get PostgreSQL connection"""
        try:
            import psycopg2
            from psycopg2 import pool
        except ImportError:
            raise ImportError("psycopg2 not installed. Run: pip install psycopg2-binary")

        conn_params = config['connection']
        settings = self.config['database_settings']['postgresql']

        # Create connection pool
        connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=settings['pool_size'],
            host=conn_params['host'],
            port=conn_params['port'],
            database=conn_params['database'],
            user=conn_params['user'],
            password=conn_params['password'],
            sslmode=conn_params.get('sslmode', 'prefer')
        )

        return connection_pool

    def _get_mssql_connection(self, config: Dict[str, Any]):
        """Get MS SQL Server connection"""
        try:
            import pyodbc
        except ImportError:
            raise ImportError("pyodbc not installed. Run: pip install pyodbc")

        conn_params = config['connection']

        # Build connection string
        conn_str = (
            f"DRIVER={{{conn_params['driver']}}};"
            f"SERVER={conn_params['server']},{conn_params['port']};"
            f"DATABASE={conn_params['database']};"
            f"UID={conn_params['user']};"
            f"PWD={conn_params['password']};"
        )

        if conn_params.get('encrypt'):
            conn_str += "Encrypt=yes;"
        if conn_params.get('trust_server_certificate'):
            conn_str += "TrustServerCertificate=yes;"

        conn = pyodbc.connect(conn_str)
        return conn

    def execute_query(self, tenant_id: str, query: str, params: tuple = None) -> list:
        """
        Execute query on tenant database

        Args:
            tenant_id: Tenant identifier
            query: SQL query
            params: Query parameters

        Returns:
            Query results as list of tuples
        """
        conn = self.get_connection(tenant_id)
        tenant_config = self.config['tenants'][tenant_id]
        db_type = tenant_config['database_type']

        if db_type == 'duckdb':
            result = conn.execute(query, params or []).fetchall()
        elif db_type == 'postgresql':
            pg_conn = conn.getconn()
            try:
                cursor = pg_conn.cursor()
                cursor.execute(query, params)
                result = cursor.fetchall()
                cursor.close()
            finally:
                conn.putconn(pg_conn)
        elif db_type == 'mssql':
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            cursor.close()
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        return result

    def get_tenant_config(self, tenant_id: str) -> DatabaseConnection:
        """Get full tenant configuration"""
        tenant_config = self.config['tenants'].get(tenant_id)
        if not tenant_config:
            raise ValueError(f"Tenant {tenant_id} not found")

        features = self.config['features'].get(tenant_id, {})

        return DatabaseConnection(
            tenant_id=tenant_id,
            tenant_name=tenant_config['name'],
            db_type=tenant_config['database_type'],
            connection_params=tenant_config['connection'],
            features=features
        )

    def get_all_tenants(self) -> list:
        """Get list of all configured tenants"""
        return list(self.config['tenants'].keys())

    def close_all_connections(self):
        """Close all database connections"""
        for tenant_id, conn in self.connections.items():
            try:
                tenant_config = self.config['tenants'][tenant_id]
                db_type = tenant_config['database_type']

                if db_type == 'duckdb':
                    conn.close()
                elif db_type == 'postgresql':
                    conn.closeall()
                elif db_type == 'mssql':
                    conn.close()
            except Exception as e:
                print(f"Error closing connection for {tenant_id}: {e}")

        self.connections.clear()


# Convenience functions
def get_db_manager(config_path: str = "config/database_config.yaml") -> MultiDatabaseManager:
    """Get singleton database manager instance"""
    return MultiDatabaseManager(config_path)


def execute_tenant_query(tenant_id: str, query: str, params: tuple = None) -> list:
    """Execute query on tenant database"""
    manager = get_db_manager()
    return manager.execute_query(tenant_id, query, params)
