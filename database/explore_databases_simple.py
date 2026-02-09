"""
Simple Database Exploration Script (Windows Compatible)
Shows current state of both databases
"""
import sqlite3
import duckdb
from pathlib import Path

USERS_DB = Path(__file__).parent / "users.db"
ANALYTICS_DB = Path(__file__).parent / "cpg_multi_tenant.duckdb"


def explore_users_db():
    """Explore SQLite users database"""
    print("\n" + "="*80)
    print("DATABASE 1: USERS.DB (SQLite - Authentication & RBAC)")
    print("="*80 + "\n")

    if not USERS_DB.exists():
        print("[ERROR] users.db not found. Run create_user_db.py first")
        return

    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()

    # Show clients
    print("\nCLIENT CONFIGURATIONS:")
    print("-" * 80)
    cursor.execute("SELECT client_id, client_name, schema_name, config_path FROM clients")
    clients = cursor.fetchall()

    print(f"{'Client ID':<15} {'Client Name':<25} {'Schema Name':<20} {'Config Path':<30}")
    print("-" * 80)
    for row in clients:
        print(f"{row[0]:<15} {row[1]:<25} {row[2]:<20} {row[3]:<30}")

    print(f"\nTotal Clients: {len(clients)}\n")

    # Show users
    print("\nACTIVE USERS:")
    print("-" * 80)
    cursor.execute("""
        SELECT username, client_id, role, full_name, email
        FROM users
        WHERE is_active = 1
        ORDER BY client_id, role
    """)
    users = cursor.fetchall()

    print(f"{'Username':<20} {'Client ID':<15} {'Role':<10} {'Full Name':<20} {'Email':<30}")
    print("-" * 80)
    for row in users:
        print(f"{row[0]:<20} {row[1]:<15} {row[2]:<10} {row[3]:<20} {row[4]:<30}")

    print(f"\nTotal Active Users: {len(users)}\n")

    # Show recent audit logs
    print("\nRECENT AUDIT LOGS (Last 10):")
    print("-" * 80)
    cursor.execute("""
        SELECT username, client_id, question, success, timestamp
        FROM audit_log
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    logs = cursor.fetchall()

    if logs:
        print(f"{'Username':<20} {'Client':<12} {'Question':<35} {'Success':<8} {'Timestamp':<20}")
        print("-" * 80)
        for row in logs:
            username, client_id, question, success, timestamp = row
            success_str = "YES" if success else "NO"
            question_short = (question[:32] + '...') if len(question) > 35 else question
            print(f"{username:<20} {client_id:<12} {question_short:<35} {success_str:<8} {timestamp:<20}")
    else:
        print("No audit logs yet")

    conn.close()


def explore_analytics_db():
    """Explore DuckDB analytics database"""
    print("\n" + "="*80)
    print("DATABASE 2: CPG_MULTI_TENANT.DUCKDB (DuckDB - Analytics Data)")
    print("="*80 + "\n")

    if not ANALYTICS_DB.exists():
        print("[ERROR] cpg_multi_tenant.duckdb not found. Run create_multi_schema_demo.py first")
        return

    conn = duckdb.connect(str(ANALYTICS_DB), read_only=True)

    # Show schemas
    print("\nSCHEMAS (Multi-Tenant Isolation):")
    print("-" * 80)
    schemas = conn.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'client_%'").fetchall()

    print(f"{'Schema Name':<20} {'Purpose':<50}")
    print("-" * 80)
    for schema in schemas:
        schema_name = schema[0]
        client_name = schema_name.replace('client_', '').title()
        print(f"{schema_name:<20} Isolated data for {client_name}")

    print(f"\nTotal Client Schemas: {len(schemas)}\n")

    # For each schema, show tables and row counts
    for schema in schemas:
        schema_name = schema[0]
        print(f"\n{'='*80}")
        print(f"SCHEMA: {schema_name.upper()}")
        print(f"{'='*80}")

        # Get tables in schema
        tables = conn.execute(f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = '{schema_name}'
            ORDER BY table_name
        """).fetchall()

        print(f"{'Table Name':<30} {'Row Count':<15} {'Type':<15}")
        print("-" * 80)
        for tbl in tables:
            table_name = tbl[0]
            count = conn.execute(f"SELECT COUNT(*) FROM {schema_name}.{table_name}").fetchone()[0]
            table_type = "Fact" if table_name.startswith('fact_') else "Dimension"
            print(f"{table_name:<30} {count:<15} {table_type:<15}")

        # Show sample data from fact table
        fact_table = [t[0] for t in tables if t[0].startswith('fact_')]
        if fact_table:
            print(f"\nSample Data from {fact_table[0]}:")
            print("-" * 80)
            sample = conn.execute(f"""
                SELECT
                    invoice_number,
                    invoice_date,
                    invoice_value,
                    net_value,
                    invoice_quantity
                FROM {schema_name}.{fact_table[0]}
                LIMIT 5
            """).fetchall()

            print(f"{'Invoice #':<20} {'Date':<15} {'Invoice Value':<15} {'Net Value':<15} {'Quantity':<10}")
            print("-" * 80)
            for row in sample:
                print(f"{str(row[0]):<20} {str(row[1]):<15} {row[2]:>14,.2f} {row[3]:>14,.2f} {row[4]:>9}")

        print()

    conn.close()


def show_database_sizes():
    """Show file sizes"""
    print("\n" + "="*80)
    print("DATABASE FILE SIZES")
    print("="*80 + "\n")

    print(f"{'Database File':<30} {'Size':<20} {'Purpose':<30}")
    print("-" * 80)

    if USERS_DB.exists():
        size_kb = USERS_DB.stat().st_size / 1024
        print(f"{'users.db':<30} {f'{size_kb:.2f} KB':<20} {'Authentication, RBAC, Audit':<30}")

    if ANALYTICS_DB.exists():
        size_kb = ANALYTICS_DB.stat().st_size / 1024
        print(f"{'cpg_multi_tenant.duckdb':<30} {f'{size_kb:.2f} KB':<20} {'Multi-tenant analytics data':<30}")

    print()


def main():
    """Main exploration"""
    print("\n" + "="*80)
    print("DATABASE EXPLORATION TOOL")
    print("Showing current state of all databases")
    print("="*80)

    show_database_sizes()
    explore_users_db()
    explore_analytics_db()

    print("\n" + "="*80)
    print("[OK] EXPLORATION COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
