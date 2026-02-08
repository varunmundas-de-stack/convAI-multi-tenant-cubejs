"""
Create user database for RBAC
Users are mapped to clients and can only query their assigned schema
"""
import sqlite3
import bcrypt
from pathlib import Path

DB_PATH = Path(__file__).parent / "users.db"


def create_user_database():
    """Create user database with authentication tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            client_id TEXT NOT NULL,
            role TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)

    # Clients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            client_id TEXT PRIMARY KEY,
            client_name TEXT NOT NULL,
            schema_name TEXT NOT NULL,
            database_path TEXT NOT NULL,
            config_path TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Audit log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            client_id TEXT NOT NULL,
            question TEXT NOT NULL,
            sql_query TEXT,
            success BOOLEAN NOT NULL,
            error_message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    return conn


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def create_sample_data(conn):
    """Create sample clients and users for testing"""
    cursor = conn.cursor()

    # Sample clients
    clients = [
        ('nestle', 'Nestlé India', 'client_nestle',
         'database/cpg_multi_tenant.duckdb',
         'semantic_layer/configs/client_nestle.yaml'),
        ('unilever', 'Unilever India', 'client_unilever',
         'database/cpg_multi_tenant.duckdb',
         'semantic_layer/configs/client_unilever.yaml'),
        ('itc', 'ITC Limited', 'client_itc',
         'database/cpg_multi_tenant.duckdb',
         'semantic_layer/configs/client_itc.yaml'),
    ]

    for client in clients:
        cursor.execute("""
            INSERT OR IGNORE INTO clients
            (client_id, client_name, schema_name, database_path, config_path)
            VALUES (?, ?, ?, ?, ?)
        """, client)

    # Sample users (one per client)
    users = [
        # Nestle users
        ('nestle_admin', 'nestle123', 'admin@nestle.com',
         'Nestle Admin', 'nestle', 'admin'),
        ('nestle_analyst', 'analyst123', 'analyst@nestle.com',
         'Nestle Analyst', 'nestle', 'analyst'),

        # Unilever users
        ('unilever_admin', 'unilever123', 'admin@unilever.com',
         'Unilever Admin', 'unilever', 'admin'),
        ('unilever_analyst', 'analyst123', 'analyst@unilever.com',
         'Unilever Analyst', 'unilever', 'analyst'),

        # ITC users
        ('itc_admin', 'itc123', 'admin@itc.com',
         'ITC Admin', 'itc', 'admin'),
        ('itc_analyst', 'analyst123', 'analyst@itc.com',
         'ITC Analyst', 'itc', 'analyst'),
    ]

    for username, password, email, full_name, client_id, role in users:
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT OR IGNORE INTO users
            (username, password_hash, email, full_name, client_id, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, password_hash, email, full_name, client_id, role))

    conn.commit()
    print("✅ User database created successfully!")
    print("\n" + "="*70)
    print("📋 SAMPLE USERS CREATED")
    print("="*70)
    print(f"{'Username':<20} {'Password':<15} {'Client':<15} {'Role':<10}")
    print("="*70)
    for username, password, _, _, client_id, role in users:
        print(f"{username:<20} {password:<15} {client_id:<15} {role:<10}")
    print("="*70)


if __name__ == "__main__":
    print("Creating user database for RBAC...")
    conn = create_user_database()
    create_sample_data(conn)
    conn.close()
    print(f"\n✅ Database created at: {DB_PATH}")
    print(f"✅ File size: {DB_PATH.stat().st_size / 1024:.2f} KB")
