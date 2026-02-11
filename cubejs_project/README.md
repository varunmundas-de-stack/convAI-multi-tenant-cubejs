# Cube.js Project for BFSI Analytics

## Overview
This Cube.js project provides a semantic layer and API for the BFSI OLAP database.

## Setup
```bash
# Install dependencies (already done during project creation)
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Access
- **Development UI:** http://localhost:4000
- **REST API:** http://localhost:4000/cubejs-api/v1
- **GraphQL API:** http://localhost:4000/cubejs-api/graphql

## Project Structure
```
cubejs_project/
├── model/
│   └── cubes/              # Cube schema definitions
│       ├── Transactions.js # Transaction fact cube
│       ├── Customers.js    # Customer dimension cube
│       ├── Dates.js        # Date dimension cube
│       ├── Accounts.js     # Account dimension cube
│       └── TransactionTypes.js # Transaction type dimension cube
├── .env                    # Environment configuration
├── cube.js                 # Cube.js config file
└── package.json
```

## Cubes

### Fact Cubes
- **Transactions** - Transaction fact table with measures like total_amount, average_amount, count

### Dimension Cubes
- **Customers** - Customer dimension with demographics and segments
- **Accounts** - Account dimension with types and regions
- **Dates** - Date dimension with year, quarter, month hierarchies
- **TransactionTypes** - Transaction type classifications

## Pre-Aggregations
Configured for optimal query performance:
- Daily transaction summaries (refreshed hourly)
- Monthly transaction summaries (refreshed daily)

## Database Connection
- Type: DuckDB
- Path: D:/lamdazen/convAI-multi-tenant-cubejs/database/bfsi_olap.duckdb
- Schema: main

## API Examples

### REST API
```bash
# Get total transactions by month
curl -G \
  -H "Authorization: YOUR_API_SECRET" \
  --data-urlencode 'query={"measures":["Transactions.count"],"timeDimensions":[{"dimension":"Dates.date","granularity":"month"}]}' \
  http://localhost:4000/cubejs-api/v1/load
```

### GraphQL API
```graphql
query {
  cube(
    measures: ["Transactions.total_amount"]
    dimensions: ["Customers.customer_segment"]
  ) {
    Customers {
      customer_segment
    }
    Transactions {
      total_amount
    }
  }
}
```

## Multi-Tenancy Support
Cube.js supports multi-tenancy through:
- Security context (configured in cube.js)
- Row-level security filters
- Tenant-specific pre-aggregations
