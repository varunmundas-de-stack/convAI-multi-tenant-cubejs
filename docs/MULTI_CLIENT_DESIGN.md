# Multi-Client/Multi-Schema Design Document

## Overview

This document outlines the strategy for supporting multiple clients with different schemas in the Conv-AI system.

## Problem Statement

**Current State:**
- Single config file: `config_cpg.yaml`
- Single DuckDB database: `cpg_olap.duckdb`
- Hardcoded system prompt in Python code
- No client isolation

**Requirements:**
1. Support multiple clients with different:
   - ERP systems (SAP, Oracle, custom)
   - Data schemas (different table/column names)
   - Business metrics (different KPIs)
   - Security rules (different data access policies)

2. Minimize code changes when onboarding new clients

3. Isolate client data and configurations

---

## Solution Architecture

### Approach 1: DuckDB Multi-Schema (Recommended)

**Concept:** Use DuckDB's native schema support to create isolated namespaces within a single database.

```
cpg_multi_tenant.duckdb
├── client_nestle/          ← Schema for Nestle
│   ├── fact_secondary_sales
│   ├── dim_product
│   ├── dim_geography
│   └── ...
├── client_unilever/        ← Schema for Unilever
│   ├── fact_sales          ← Different table name!
│   ├── dim_product
│   └── ...
└── client_itc/
    ├── fact_transactions   ← Another different name!
    └── ...
```

**Benefits:**
- ✅ Single database file (easier deployment)
- ✅ True data isolation (schemas can't access each other)
- ✅ Fast queries (no cross-database joins needed)
- ✅ Easy backup/restore (one file)
- ✅ DuckDB supports full SQL in each schema

**Implementation Steps:**

1. **Create schemas in DuckDB:**
```sql
-- Create client schemas
CREATE SCHEMA client_nestle;
CREATE SCHEMA client_unilever;
CREATE SCHEMA client_itc;

-- Create tables in each schema
CREATE TABLE client_nestle.fact_secondary_sales (...);
CREATE TABLE client_unilever.fact_sales (...);
CREATE TABLE client_itc.fact_transactions (...);
```

2. **Config file per client:**
```
semantic_layer/
├── configs/
│   ├── client_nestle.yaml       ← Nestle-specific config
│   ├── client_unilever.yaml     ← Unilever-specific config
│   └── client_itc.yaml          ← ITC-specific config
└── config_cpg.yaml              ← Default/template
```

**Sample `client_nestle.yaml`:**
```yaml
client:
  id: "nestle"
  name: "Nestlé India"
  schema: "client_nestle"        # DuckDB schema name

database:
  path: "database/cpg_multi_tenant.duckdb"
  type: "duckdb"
  schema: "client_nestle"         # Important: schema prefix

metrics:
  secondary_sales_value:
    description: "Net invoiced value to retailers"
    sql: "SUM(net_value)"
    table: "client_nestle.fact_secondary_sales"  # Schema-qualified table
    aggregation: "sum"
    format: "currency"

dimensions:
  product:
    levels:
      - name: "brand_name"
        table: "client_nestle.dim_product"      # Schema-qualified
        column: "brand_name"
```

3. **Modify SemanticLayer to support schemas:**

**File: `semantic_layer/semantic_layer.py`**
```python
class SemanticLayer:
    def __init__(self, config_path: str, client_id: Optional[str] = None):
        """
        Args:
            config_path: Path to config file or directory
            client_id: Client identifier (if multi-tenant)
        """
        if client_id:
            # Load client-specific config
            config_path = f"semantic_layer/configs/client_{client_id}.yaml"

        self.config = self._load_config(config_path)
        self.client_id = client_id
        self.db_schema = self.config.get('client', {}).get('schema', 'public')

    def _qualify_table_name(self, table_name: str) -> str:
        """Add schema prefix to table names"""
        if '.' not in table_name and self.db_schema:
            return f"{self.db_schema}.{table_name}"
        return table_name

    def get_metric(self, metric_name: str) -> dict:
        metric = self.metrics.get(metric_name)
        if metric:
            # Ensure table is schema-qualified
            metric['table'] = self._qualify_table_name(metric['table'])
        return metric
```

4. **Modify Intent Parser to load client-specific config:**

**File: `llm/intent_parser_v2.py`**
```python
class IntentParserV2:
    def __init__(self, semantic_layer: SemanticLayer, client_id: str = None, ...):
        self.client_id = client_id
        # Load client-specific system prompt
        self.system_prompt = self._load_system_prompt(client_id)

    def _load_system_prompt(self, client_id: str) -> str:
        """Load client-specific system prompt from config"""
        if client_id:
            prompt_path = f"semantic_layer/prompts/client_{client_id}_prompt.txt"
            if os.path.exists(prompt_path):
                with open(prompt_path) as f:
                    return f.read()
        # Fallback to default
        return self._get_default_system_prompt()
```

5. **Modify Flask app to support client selection:**

**File: `frontend/app.py`**
```python
# Initialize with client context
client_id = os.getenv('CLIENT_ID', 'nestle')  # From env var or request header

semantic_layer = SemanticLayer(
    config_path=f"semantic_layer/configs/client_{client_id}.yaml",
    client_id=client_id
)

# Or support multi-tenant in same app:
@app.before_request
def load_client_context():
    client_id = request.headers.get('X-Client-ID', 'default')
    g.semantic_layer = get_semantic_layer(client_id)  # Cache per client
```

---

### Approach 2: Separate Databases (Alternative)

**Concept:** One DuckDB file per client

```
database/
├── client_nestle.duckdb
├── client_unilever.duckdb
└── client_itc.duckdb
```

**Benefits:**
- ✅ Complete isolation
- ✅ Independent backups
- ✅ Easy to scale (move to different servers)

**Drawbacks:**
- ❌ More files to manage
- ❌ Can't do cross-client analytics
- ❌ More complex deployment

---

## Testing Strategy

### Phase 1: Create Test Schemas

**Script: `database/create_multi_schema.py`**
```python
import duckdb

conn = duckdb.connect('database/cpg_multi_tenant.duckdb')

# Create schemas
conn.execute("CREATE SCHEMA IF NOT EXISTS client_nestle")
conn.execute("CREATE SCHEMA IF NOT EXISTS client_unilever")

# Nestle schema - CPG secondary sales
conn.execute("""
    CREATE TABLE client_nestle.fact_secondary_sales (
        invoice_key INTEGER PRIMARY KEY,
        invoice_date DATE,
        product_key INTEGER,
        geography_key INTEGER,
        net_value DECIMAL(12,2),
        invoice_quantity INTEGER
    )
""")

# Unilever schema - Different naming convention!
conn.execute("""
    CREATE TABLE client_unilever.fact_sales (  -- Different table name
        sale_id INTEGER PRIMARY KEY,
        sale_date DATE,
        product_id INTEGER,
        region_id INTEGER,
        revenue DECIMAL(12,2),           -- Different column name!
        units_sold INTEGER
    )
""")

print("✅ Multi-schema database created!")
```

### Phase 2: Create Client Configs

**File: `semantic_layer/configs/client_nestle.yaml`**
```yaml
client:
  id: "nestle"
  name: "Nestlé India"
  schema: "client_nestle"

database:
  path: "database/cpg_multi_tenant.duckdb"
  schema: "client_nestle"

metrics:
  secondary_sales_value:
    sql: "SUM(net_value)"
    table: "fact_secondary_sales"  # Auto-prefixed to client_nestle.fact_secondary_sales
```

**File: `semantic_layer/configs/client_unilever.yaml`**
```yaml
client:
  id: "unilever"
  name: "Unilever India"
  schema: "client_unilever"

database:
  path: "database/cpg_multi_tenant.duckdb"
  schema: "client_unilever"

metrics:
  sales_revenue:                    # Different metric name!
    sql: "SUM(revenue)"             # Different column name!
    table: "fact_sales"             # Different table name!
```

### Phase 3: Test Client Isolation

**Test Script: `tests/test_multi_client.py`**
```python
def test_nestle_query():
    sl = SemanticLayer(config_path="...", client_id="nestle")
    # Should query client_nestle.fact_secondary_sales
    assert sl.db_schema == "client_nestle"

def test_unilever_query():
    sl = SemanticLayer(config_path="...", client_id="unilever")
    # Should query client_unilever.fact_sales
    assert sl.db_schema == "client_unilever"

def test_cross_client_isolation():
    # Nestle user should NOT see Unilever data
    sl_nestle = SemanticLayer(client_id="nestle")
    result = sl_nestle.execute_query("SELECT * FROM fact_sales")
    # Should fail or return 0 rows (table not in nestle schema)
```

---

## Configuration Management

### Option 1: Environment Variables
```bash
# Production deployment
CLIENT_ID=nestle
CONFIG_PATH=semantic_layer/configs/client_nestle.yaml
DB_SCHEMA=client_nestle
```

### Option 2: Client Registry
**File: `semantic_layer/client_registry.yaml`**
```yaml
clients:
  nestle:
    config: "semantic_layer/configs/client_nestle.yaml"
    schema: "client_nestle"
    database: "database/cpg_multi_tenant.duckdb"

  unilever:
    config: "semantic_layer/configs/client_unilever.yaml"
    schema: "client_unilever"
    database: "database/cpg_multi_tenant.duckdb"
```

Then load dynamically:
```python
registry = yaml.safe_load(open('semantic_layer/client_registry.yaml'))
client_config = registry['clients'][client_id]
semantic_layer = SemanticLayer(config_path=client_config['config'])
```

---

## Migration Path for New Clients

### Step 1: Extract Source Schema
```python
# Connect to client's SAP/Oracle/etc
import pandas as pd

# Extract table metadata
tables = pd.read_sql("SELECT table_name FROM information_schema.tables WHERE schema='sap_sales'", client_conn)

# Generate config template
for table in tables:
    print(f"  {table}:")
    print(f"    table: 'client_xyz.{table}'")
```

### Step 2: Map to Semantic Layer
```yaml
# Client XYZ uses SAP - different column names
metrics:
  secondary_sales_value:
    sql: "SUM(netwr)"              # SAP field name: NETWR
    table: "fact_vbrk_vbrp"        # SAP tables: VBRK + VBRP
```

### Step 3: Generate Sample Data (for testing)
```python
# Generate 1000 rows matching client schema
python database/generate_client_data.py --client xyz --rows 1000
```

### Step 4: Test Queries
```bash
# Run test suite for new client
pytest tests/test_client_xyz.py
```

### Step 5: Deploy
```bash
# Deploy with client context
export CLIENT_ID=xyz
python frontend/app.py
```

---

## Estimated Effort for New Client Onboarding

| Task | Estimated Time | Changed Files |
|------|---------------|---------------|
| **Schema analysis** | 2-4 hours | - |
| **Create DuckDB schema** | 1 hour | `create_schema.sql` |
| **Map metrics to tables** | 4-8 hours | `client_xyz.yaml` |
| **Create system prompt** | 2 hours | `client_xyz_prompt.txt` |
| **Generate test data** | 2 hours | `generate_client_data.py` |
| **Test queries** | 4-6 hours | `test_client_xyz.py` |
| **Deploy configuration** | 1 hour | `.env`, `client_registry.yaml` |
| **TOTAL** | **16-24 hours** | **~5 files** |

**Key Point:** Zero Python code changes needed after initial multi-client refactoring!

---

## Security Considerations

### 1. Schema-Level Security
```sql
-- Create read-only user per client
CREATE USER nestle_readonly WITH PASSWORD 'xxxx';
GRANT USAGE ON SCHEMA client_nestle TO nestle_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA client_nestle TO nestle_readonly;
```

### 2. Config File Security
- Store configs outside Git repo
- Use environment variables for sensitive values
- Encrypt config files at rest

### 3. Row-Level Security (RLS)
```yaml
# In client config
security:
  rls_enabled: true
  filters:
    - dimension: "state_name"
      allowed_values: ["Tamil Nadu", "Karnataka"]  # User-specific
```

---

## Summary

**Answer to Question 2:**

> **"Given that source schema will vary with each client/ERP-DW, is it that only config.yaml file will require changes and then some amount of testing?"**

**YES**, with the multi-schema approach:

1. ✅ **Only config changes needed:**
   - `client_xyz.yaml` - Maps business metrics to client schema
   - `client_xyz_prompt.txt` - Client-specific LLM prompt
   - `client_registry.yaml` - Client metadata

2. ✅ **Minimal code changes:**
   - One-time refactoring to support `client_id` parameter
   - Add schema qualification logic (`client_xyz.table_name`)
   - After that, **zero code changes** for new clients

3. ✅ **Testing required:**
   - Schema validation (tables/columns exist)
   - Query accuracy (correct results)
   - Performance testing (query speed)
   - Security testing (data isolation)
   - Estimated: 4-6 hours per client

4. ✅ **DuckDB Multi-Schema Benefits:**
   - True data isolation
   - Single database file (easy deployment)
   - Fast queries (no cross-DB overhead)
   - Standard SQL support

**Onboarding Time:** 16-24 hours per client (mostly config and testing, no coding)

