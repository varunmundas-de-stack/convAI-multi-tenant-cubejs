"""
Database Exploration Script
Shows current state of both databases (users.db + cpg_multi_tenant.duckdb)
"""
import sqlite3
import duckdb
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

USERS_DB = Path(__file__).parent / "users.db"
ANALYTICS_DB = Path(__file__).parent / "cpg_multi_tenant.duckdb"


def explore_users_db():
    """Explore SQLite users database"""
    console.print("\n" + "="*80, style="bold cyan")
    console.print("DATABASE 1: USERS.DB (SQLite - Authentication & RBAC)", style="bold cyan")
    console.print("="*80 + "\n", style="bold cyan")

    if not USERS_DB.exists():
        console.print("[red]Error: users.db not found. Run create_user_db.py first[/red]")
        return

    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()

    # Show clients
    console.print(Panel.fit("CLIENT CONFIGURATIONS", style="bold green"))
    cursor.execute("SELECT client_id, client_name, schema_name, config_path FROM clients")
    clients = cursor.fetchall()

    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Client ID", style="cyan")
    table.add_column("Client Name", style="green")
    table.add_column("Schema Name", style="yellow")
    table.add_column("YAML Config Path", style="blue")

    for row in clients:
        table.add_row(*row)

    console.print(table)
    console.print(f"\n[green]Total Clients: {len(clients)}[/green]\n")

    # Show users
    console.print(Panel.fit("ACTIVE USERS", style="bold green"))
    cursor.execute("""
        SELECT username, client_id, role, full_name, email
        FROM users
        WHERE is_active = 1
        ORDER BY client_id, role
    """)
    users = cursor.fetchall()

    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Username", style="cyan")
    table.add_column("Client ID", style="green")
    table.add_column("Role", style="yellow")
    table.add_column("Full Name", style="blue")
    table.add_column("Email", style="white")

    for row in users:
        table.add_row(*row)

    console.print(table)
    console.print(f"\n[green]Total Active Users: {len(users)}[/green]\n")

    # Show recent audit logs
    console.print(Panel.fit("RECENT AUDIT LOGS (Last 10)", style="bold green"))
    cursor.execute("""
        SELECT username, client_id, question, success, timestamp
        FROM audit_log
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    logs = cursor.fetchall()

    if logs:
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Username", style="cyan")
        table.add_column("Client", style="green")
        table.add_column("Question", style="yellow", max_width=40)
        table.add_column("Success", style="blue")
        table.add_column("Timestamp", style="white")

        for row in logs:
            username, client_id, question, success, timestamp = row
            success_str = "✓" if success else "✗"
            table.add_row(username, client_id, question, success_str, timestamp)

        console.print(table)
    else:
        console.print("[yellow]No audit logs yet[/yellow]")

    conn.close()


def explore_analytics_db():
    """Explore DuckDB analytics database"""
    console.print("\n" + "="*80, style="bold cyan")
    console.print("DATABASE 2: CPG_MULTI_TENANT.DUCKDB (DuckDB - Analytics Data)", style="bold cyan")
    console.print("="*80 + "\n", style="bold cyan")

    if not ANALYTICS_DB.exists():
        console.print("[red]Error: cpg_multi_tenant.duckdb not found. Run create_multi_schema_demo.py first[/red]")
        return

    conn = duckdb.connect(str(ANALYTICS_DB), read_only=True)

    # Show schemas
    console.print(Panel.fit("SCHEMAS (Multi-Tenant Isolation)", style="bold green"))
    schemas = conn.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'client_%'").fetchall()

    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Schema Name", style="cyan")
    table.add_column("Purpose", style="yellow")

    for schema in schemas:
        schema_name = schema[0]
        client_name = schema_name.replace('client_', '').title()
        table.add_row(schema_name, f"Isolated data for {client_name}")

    console.print(table)
    console.print(f"\n[green]Total Client Schemas: {len(schemas)}[/green]\n")

    # For each schema, show tables and row counts
    for schema in schemas:
        schema_name = schema[0]
        console.print(Panel.fit(f"SCHEMA: {schema_name.upper()}", style="bold yellow"))

        # Get tables in schema
        tables = conn.execute(f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = '{schema_name}'
            ORDER BY table_name
        """).fetchall()

        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Table Name", style="cyan")
        table.add_column("Row Count", style="green")
        table.add_column("Type", style="yellow")

        for tbl in tables:
            table_name = tbl[0]
            count = conn.execute(f"SELECT COUNT(*) FROM {schema_name}.{table_name}").fetchone()[0]
            table_type = "Fact" if table_name.startswith('fact_') else "Dimension"
            table.add_row(table_name, str(count), table_type)

        console.print(table)

        # Show sample data from fact table
        fact_table = [t[0] for t in tables if t[0].startswith('fact_')]
        if fact_table:
            console.print(f"\n[bold]Sample Data from {fact_table[0]}:[/bold]")
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

            sample_table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
            sample_table.add_column("Invoice #")
            sample_table.add_column("Date")
            sample_table.add_column("Invoice Value")
            sample_table.add_column("Net Value")
            sample_table.add_column("Quantity")

            for row in sample:
                sample_table.add_row(
                    str(row[0]),
                    str(row[1]),
                    f"{row[2]:,.2f}",
                    f"{row[3]:,.2f}",
                    str(row[4])
                )

            console.print(sample_table)

        console.print()

    conn.close()


def show_database_sizes():
    """Show file sizes"""
    console.print("\n" + "="*80, style="bold cyan")
    console.print("DATABASE FILE SIZES", style="bold cyan")
    console.print("="*80 + "\n", style="bold cyan")

    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Database File", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Purpose", style="yellow")

    if USERS_DB.exists():
        size_kb = USERS_DB.stat().st_size / 1024
        table.add_row("users.db", f"{size_kb:.2f} KB", "Authentication, RBAC, Audit")

    if ANALYTICS_DB.exists():
        size_kb = ANALYTICS_DB.stat().st_size / 1024
        table.add_row("cpg_multi_tenant.duckdb", f"{size_kb:.2f} KB", "Multi-tenant analytics data")

    console.print(table)
    console.print()


def main():
    """Main exploration"""
    console.print("\n[bold cyan]DATABASE EXPLORATION TOOL[/bold cyan]")
    console.print("[dim]Showing current state of all databases[/dim]\n")

    show_database_sizes()
    explore_users_db()
    explore_analytics_db()

    console.print("\n" + "="*80, style="bold green")
    console.print("[OK] EXPLORATION COMPLETE", style="bold green")
    console.print("="*80 + "\n", style="bold green")


if __name__ == "__main__":
    main()
