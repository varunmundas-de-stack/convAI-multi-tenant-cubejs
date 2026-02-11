# dbt Project for Sales Analytics

## Overview
This dbt project provides transformation logic for the BFSI OLAP database.

## Setup
```bash
# Install dbt with DuckDB adapter
pip install dbt-duckdb

# Navigate to project
cd dbt_project/sales_analytics

# Test connection
dbt debug

# Run models
dbt run

# Generate documentation
dbt docs generate
dbt docs serve
```

## Project Structure
```
sales_analytics/
├── models/
│   ├── staging/          # Staging models (views)
│   │   ├── sources.yml   # Source definitions
│   │   └── stg_*.sql     # Staging models
│   └── marts/            # Mart models (tables)
│       └── fct_*.sql     # Fact tables
├── dbt_project.yml       # Project configuration
└── profiles.yml          # Connection configuration (in ~/.dbt/)
```

## Models

### Staging Layer
- `stg_transactions` - Cleaned transaction data

### Marts Layer
- `fct_daily_transactions` - Daily transaction summary with aggregates

## Configuration
Database connection configured in `~/.dbt/profiles.yml`:
- Database: DuckDB
- Path: D:\lamdazen\convAI-multi-tenant-cubejs\database\bfsi_olap.duckdb
- Schema: main
