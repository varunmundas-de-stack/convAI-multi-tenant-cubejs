# Testing Guide - CPG Conversational AI (RelDB-Only)

> ⚠️ **Note**: This is the **RelDB-Only** version using DuckDB only. For the ChromaDB version with semantic search testing, see [Conv-AI-ChromaDB](https://github.com/varunmundas-de-stack/Conv-AI-ChromaDB).

## Quick Test Checklist

- [ ] DuckDB database exists and has data
- [ ] Flask web app starts successfully
- [ ] Sample queries return results
- [ ] SQL queries are generated correctly
- [ ] Audit logs are created

## 1. Verify DuckDB Data

### Check Database File

```bash
ls -lh database/cpg_olap.duckdb
```

**Expected:** File exists (around 100KB)

### Check Table Counts

```bash
python -c "import duckdb; conn = duckdb.connect('database/cpg_olap.duckdb'); print('Sales:', conn.execute('SELECT COUNT(*) FROM fact_sales').fetchone()[0]); print('Products:', conn.execute('SELECT COUNT(*) FROM dim_product').fetchone()[0]); print('Dates:', conn.execute('SELECT COUNT(*) FROM dim_date').fetchone()[0])"
```

**Expected output:**
```
Sales: 1000
Products: 50
Dates: 90
```

## 2. Test Query Types

### Test 1: Ranking Query

**Question:** "Show top 5 brands by sales value"

**Expected Result:**
- Table with 5 rows
- Columns: Brand, Sales Value
- Values sorted descending
- SQL query shown (collapsible)

### Test 2: Trend Analysis

**Question:** "Weekly sales trend for last 6 weeks"

**Expected Result:**
- Table with 6 rows
- Columns: Week, Sales Value
- Chronological order
- Parse time < 200ms

### Test 3: Snapshot Query

**Question:** "Total sales this month"

**Expected Result:**
- Single value
- Shows current month sales
- Fast execution (< 100ms)

### Test 4: Diagnostic Query

**Question:** "Why did sales change?"

**Expected Result:**
- Trend analysis section
- Key insights
- Recommendations
- Contribution analysis
- Multiple queries executed

### Test 5: Filtered Query

**Question:** "Sales by state in Tamil Nadu"

**Expected Result:**
- Filtered results for Tamil Nadu only
- Correct state name matching
- Filter applied in SQL WHERE clause

## 3. Test Error Handling

### Test: Out of Scope Question

**Question:** "What is the capital of France?"

**Expected:**
```
⚠️ Out of Scope
This chatbot answers CPG sales analytics questions only.
```

### Test: Low Confidence

**Question:** "xyzabc random text"

**Expected:**
- Error message about low confidence
- Suggestion to try examples

### Test: Invalid Metric

**Question:** "Show top brands by banana"

**Expected:**
- Validation error
- Suggestion to use valid metrics

## 4. Performance Testing

Run this script to measure query performance:

```python
import time
import requests

queries = [
    "Show top 5 brands by sales value",
    "Weekly sales trend for last 6 weeks",
    "Total sales this month",
    "Sales by state",
    "Why did sales change?"
]

print(f"{'Query':<45} {'Time (ms)':<15} {'Status':<10}")
print("-" * 70)

for query in queries:
    start = time.time()
    response = requests.post('http://localhost:5000/api/query',
                            json={'question': query})
    elapsed = (time.time() - start) * 1000

    status = "✅ OK" if response.json().get('success') else "❌ FAIL"
    print(f"{query:<45} {elapsed:<15.0f} {status:<10}")
```

**Expected Performance:**
- Ranking queries: 100-200ms
- Trend queries: 150-250ms
- Snapshot queries: 50-100ms
- Diagnostic queries: 500-800ms (multiple queries)

## 5. Test Audit Logging

```bash
# Check if audit logs are being created
cat logs/audit.jsonl | head -5
```

**Expected:**
- JSON lines format
- Each query logged
- Includes: query_id, user_id, SQL, execution time

## 6. CLI Testing

### Test CLI Query

```bash
python cli/ask.py "Show top 5 brands by sales value"
```

**Expected:**
- Results printed to console
- Formatted table output
- No errors

## 7. Cross-Verification Tests

### Verify SQL Generation

```python
from llm.intent_parser_v2 import IntentParserV2
from semantic_layer.semantic_layer import SemanticLayer
from query_engine.sql_generator import SQLGenerator

semantic_layer = SemanticLayer("semantic_layer/config_cpg.yaml")
intent_parser = IntentParserV2(semantic_layer, use_claude=False)
sql_gen = SQLGenerator(semantic_layer)

# Parse question
question = "Show top 5 brands by sales value"
semantic_query = intent_parser.parse(question)

# Generate SQL
sql = sql_gen.generate(semantic_query)
print(sql)
```

**Expected SQL:**
```sql
SELECT
    dim_product.brand_name AS brand,
    SUM(fact_sales.gross_sales_value) AS sales_value
FROM fact_sales
JOIN dim_product ON fact_sales.product_id = dim_product.product_id
GROUP BY dim_product.brand_name
ORDER BY sales_value DESC
LIMIT 5
```

## 8. Integration Test Suite

Run all automated tests:

```bash
pytest tests/
```

**Expected:**
- All tests pass
- Coverage report generated
- No warnings

## Common Issues

### Issue 1: No Results Returned

**Symptoms:** Query returns "No results found"

**Causes:**
- Empty database
- Incorrect date filters
- Wrong table joins

**Solution:**
```bash
# Regenerate database
cd database
python generate_cpg_data.py
```

### Issue 2: Intent Parsing Fails

**Symptoms:** "Sorry, I couldn't understand that question"

**Causes:**
- Ollama not running
- Model not loaded
- Typos in question

**Solution:**
```bash
# Start Ollama
ollama serve

# Pull model
ollama pull mistral
```

### Issue 3: SQL Generation Error

**Symptoms:** "Validation error" or SQL syntax error

**Causes:**
- Invalid metric names
- Missing dimensions
- Configuration error

**Solution:**
- Check `semantic_layer/config_cpg.yaml`
- Verify metric and dimension names
- Use "give me examples" to see valid queries

## Test Summary Checklist

- [ ] All query types work (ranking, trend, snapshot, diagnostic)
- [ ] Error handling works correctly
- [ ] Performance is acceptable (< 300ms for most queries)
- [ ] Audit logs are being created
- [ ] SQL generation is correct
- [ ] No Python errors in terminal

## Next Steps

After testing:
1. Review audit logs for patterns
2. Optimize slow queries
3. Add more test cases
4. Test with larger datasets
5. Test concurrent users

## Differences from ChromaDB Version

This RelDB-Only version does NOT test:
- ❌ Vector embeddings
- ❌ Semantic similarity search
- ❌ AI-Enhanced query mode
- ❌ ChromaDB Direct mode
- ❌ Similar query suggestions

For testing those features, see the [ChromaDB version](https://github.com/varunmundas-de-stack/Conv-AI-ChromaDB).
