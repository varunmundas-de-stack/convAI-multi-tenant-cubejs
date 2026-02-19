# Metabase Dashboard Integration - Setup Guide

## Overview

This guide sets up **Metabase** - an open-source Tableau alternative - to provide professional-quality dashboards for your CPG analytics system.

**Result:** Business users get beautiful, interactive dashboards with drill-downs, filters, and charts - all embedded in your Flask app.

---

## Prerequisites

1. **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop/)
   - Windows 10/11 with WSL2 enabled
   - At least 2 GB RAM allocated to Docker

2. **Existing CPG Analytics** - Your Flask app should be working
   - Database: `database/cpg_olap.duckdb`
   - Flask app: `frontend/app.py`

---

## Quick Start (5 minutes)

### Step 1: Start Services

```bash
# Double-click this file:
start_metabase.bat
```

This will:
- Start Metabase in Docker (port 3000)
- Start Flask chatbot (port 5000)
- Wait for services to be ready

### Step 2: First-Time Metabase Setup (2 minutes)

1. Open browser: http://localhost:3000
2. **Create admin account:**
   - First name: Your name
   - Email: your@email.com
   - Password: Choose a secure password
   - Company: Your company name

3. Click **"I'll add my data later"** (skip the wizard)

4. **Add database connection:**
   - Click Settings (⚙️ gear icon) → Admin → Databases
   - Click **"Add database"**
   - Select **"SQLite"** from dropdown
   - Fill in:
     ```
     Display name: CPG Analytics
     Filename: /data/cpg_olap.duckdb
     ```
   - Click **"Save"**
   - Wait for green checkmark (database connected!)

5. Click **"Exit admin"** (top right)

### Step 3: Create Your First Dashboard (5 minutes)

See "Creating Dashboards" section below.

---

## Stopping Services

```bash
# Double-click this file:
stop_metabase.bat
```

Or manually:
```bash
docker-compose -f docker-compose.metabase.yml down
```

---

## Creating Dashboards in Metabase

### Option 1: Ask a Question (Simple)

1. Click **"New"** → **"Question"**
2. Select **"CPG Analytics"** database
3. Pick a table (e.g., `fact_secondary_sales`)
4. Click **"Visualize"**
5. Metabase auto-generates a chart
6. Click **"Save"** → Name it → **"Save to dashboard"**

### Option 2: Use SQL (Advanced)

1. Click **"New"** → **"SQL query"**
2. Select **"CPG Analytics"** database
3. Write SQL:
   ```sql
   SELECT
       p.brand_name,
       SUM(s.net_value) as total_sales,
       SUM(s.invoice_quantity) as total_volume
   FROM fact_secondary_sales s
   JOIN dim_product p ON s.product_key = p.product_key
   WHERE s.return_flag = false
   GROUP BY p.brand_name
   ORDER BY total_sales DESC
   LIMIT 10
   ```
4. Click **"Visualize"** → Metabase suggests chart type
5. Customize chart (colors, labels, etc.)
6. Click **"Save"**

### Sample Dashboard Ideas

#### 1. **Sales Performance Dashboard**
- KPI cards: Total Sales, Total Volume, Avg Invoice Value
- Line chart: Sales trend by month
- Bar chart: Top 10 brands
- Pie chart: Sales by channel
- Table: Top retailers

#### 2. **Product Analytics Dashboard**
- Bar chart: Sales by category
- Bar chart: Sales by subcategory (NEW!)
- Scatter plot: Price vs Volume
- Table: Product performance with weight/volume metrics (NEW!)

#### 3. **Sales Hierarchy Dashboard** (NEW!)
- KPI cards by NSM/ZSM/ASM/SO
- Map: Sales by zone
- Bar chart: Top ASMs
- Table: SO performance by territory

#### 4. **Regional Performance**
- Map visualization: Sales by state
- Bar chart: Top zones
- Line chart: Regional trends
- Heatmap: State x Month

---

## Embedding Dashboards in Flask

Once you create dashboards in Metabase, you can embed them in your Flask app.

### Step 1: Get Embed URL

1. Open your dashboard in Metabase
2. Click **"Sharing"** icon (🔗) → **"Public link"**
3. Toggle **"Enable sharing"**
4. Copy the **public link** (e.g., `http://localhost:3000/public/dashboard/abc123`)

### Step 2: Add Iframe to Flask

**Option A: Separate Dashboard Page**

Create `frontend/templates/dashboard.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>CPG Analytics Dashboard</title>
    <style>
        body { margin: 0; padding: 0; overflow: hidden; }
        iframe { width: 100vw; height: 100vh; border: none; }
    </style>
</head>
<body>
    <iframe src="http://localhost:3000/public/dashboard/YOUR_DASHBOARD_ID"></iframe>
</body>
</html>
```

Add route in `frontend/app.py`:
```python
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
```

**Option B: Embed in Chat Interface**

Add a button in `frontend/templates/chat.html`:
```html
<button onclick="window.open('http://localhost:3000/public/dashboard/YOUR_DASHBOARD_ID', '_blank')">
    📊 View Dashboard
</button>
```

---

## Advanced Configuration

### Use PostgreSQL for Metabase Metadata (Production)

Edit `docker-compose.metabase.yml`:
1. Uncomment the `metabase-db` service
2. Update Metabase environment variables:
   ```yaml
   MB_DB_TYPE: postgres
   MB_DB_DBNAME: metabase
   MB_DB_PORT: 5432
   MB_DB_USER: metabase
   MB_DB_PASS: metabase_password
   MB_DB_HOST: metabase-db
   ```
3. Restart: `docker-compose -f docker-compose.metabase.yml up -d`

### Connect to PostgreSQL/MS SQL (Instead of DuckDB)

If using PostgreSQL or MS SQL Server:

1. In Metabase Admin → Databases → Add database
2. Select **PostgreSQL** or **SQL Server**
3. Enter connection details:
   ```
   Host: your-host
   Port: 5432 (PostgreSQL) or 1433 (SQL Server)
   Database: cpg_analytics
   Username: your_username
   Password: your_password
   ```

### Automatic Dashboard Refresh

1. Open dashboard in Metabase
2. Click **"⋮"** (three dots) → **"Auto-refresh"**
3. Select refresh interval (1 min, 5 min, 10 min, etc.)

---

## Sample Queries for CPG Analytics

### Sales Performance
```sql
SELECT
    d.month_name,
    d.year,
    SUM(s.net_value) as sales,
    SUM(s.invoice_quantity) as volume,
    COUNT(DISTINCT s.invoice_number) as invoices
FROM fact_secondary_sales s
JOIN dim_date d ON s.date_key = d.date_key
WHERE s.return_flag = false
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month
```

### Top Brands with Subcategory (NEW!)
```sql
SELECT
    p.category_name,
    p.subcategory_name,
    p.brand_name,
    SUM(s.net_value) as total_sales,
    SUM(s.invoice_quantity) as total_volume
FROM fact_secondary_sales s
JOIN dim_product p ON s.product_key = p.product_key
WHERE s.return_flag = false
GROUP BY p.category_name, p.subcategory_name, p.brand_name
ORDER BY total_sales DESC
LIMIT 20
```

### Sales by Sales Hierarchy (NEW!)
```sql
SELECT
    sh.nsm_name,
    sh.zsm_name,
    sh.asm_name,
    sh.so_name,
    sh.zone_name,
    COUNT(DISTINCT s.invoice_number) as invoices,
    SUM(s.net_value) as total_sales,
    SUM(s.invoice_quantity) as total_volume
FROM fact_secondary_sales s
JOIN dim_sales_hierarchy sh ON s.sales_hierarchy_key = sh.sales_hierarchy_key
WHERE s.return_flag = false
GROUP BY sh.nsm_name, sh.zsm_name, sh.asm_name, sh.so_name, sh.zone_name
ORDER BY total_sales DESC
```

### Weight & Volume Analysis (NEW!)
```sql
SELECT
    p.brand_name,
    SUM(s.total_weight) as total_weight_kg,
    SUM(s.total_volume) as total_volume_liters,
    SUM(s.net_value) as total_sales,
    SUM(s.net_value) / NULLIF(SUM(s.total_weight), 0) as revenue_per_kg,
    SUM(s.net_value) / NULLIF(SUM(s.total_volume), 0) as revenue_per_liter
FROM fact_secondary_sales s
JOIN dim_product p ON s.product_key = p.product_key
WHERE s.return_flag = false
  AND (s.total_weight > 0 OR s.total_volume > 0)
GROUP BY p.brand_name
ORDER BY total_sales DESC
```

### Primary Sales with Warehouse (NEW!)
```sql
SELECT
    p.companywh_name,
    c.distributor_name,
    pr.brand_name,
    COUNT(*) as order_count,
    SUM(p.order_value) as total_order_value,
    SUM(p.dispatch_value) as total_dispatched,
    SUM(p.pending_quantity) as pending_quantity
FROM fact_primary_sales p
JOIN dim_customer c ON p.customer_key = c.customer_key
JOIN dim_product pr ON p.product_key = pr.product_key
GROUP BY p.companywh_name, c.distributor_name, pr.brand_name
ORDER BY total_order_value DESC
LIMIT 20
```

---

## Troubleshooting

### Issue: "Docker is not running"
**Solution:** Start Docker Desktop from Windows Start menu

### Issue: "Port 3000 is already in use"
**Solution:**
1. Check what's using port 3000: `netstat -ano | findstr :3000`
2. Kill that process or change Metabase port in `docker-compose.metabase.yml`

### Issue: "Database connection failed"
**Solution:**
1. Check DuckDB path is correct: `/data/cpg_olap.duckdb`
2. Ensure database file exists: `ls database/cpg_olap.duckdb`
3. Try "SQLite" driver instead of "DuckDB" (Metabase treats DuckDB as SQLite)

### Issue: "Metabase is slow"
**Solution:**
1. Increase Docker memory: Docker Desktop → Settings → Resources → Memory (4 GB recommended)
2. Use pre-aggregations in Metabase (Admin → Performance)

### Issue: "Can't see new columns"
**Solution:**
1. Go to Admin → Databases → CPG Analytics
2. Click "Sync database schema now"
3. Wait for sync to complete

---

## Production Deployment

### 1. Use External PostgreSQL for Metabase Metadata
- Uncomment `metabase-db` service in docker-compose
- Or use managed PostgreSQL (AWS RDS, Azure Database, etc.)

### 2. Enable SSL
- Configure Nginx reverse proxy with SSL
- Use Let's Encrypt for free certificates

### 3. Set Strong Admin Password
- Change default password immediately
- Enable 2FA in Metabase settings

### 4. Regular Backups
```bash
# Backup Metabase data
docker-compose -f docker-compose.metabase.yml exec metabase \
  tar -czf /metabase-data/backup.tar.gz /metabase-data/metabase.db
```

### 5. Monitor Performance
- Use Metabase's built-in query analyzer
- Set up query caching (Admin → Performance)
- Create pre-aggregated tables for large datasets

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    User Browser                      │
│  ┌──────────────────┐    ┌──────────────────┐      │
│  │   Flask Chatbot   │    │ Metabase Dashboard│      │
│  │  localhost:5000   │    │  localhost:3000   │      │
│  └──────────────────┘    └──────────────────┘      │
└─────────────────────────────────────────────────────┘
           │                        │
           ▼                        ▼
  ┌─────────────────┐    ┌─────────────────┐
  │   Python Flask  │    │  Metabase       │
  │   + Semantic    │    │  (Docker)       │
  │     Layer       │    │                 │
  └─────────────────┘    └─────────────────┘
           │                        │
           └────────┬───────────────┘
                    ▼
          ┌──────────────────┐
          │  DuckDB Database │
          │  cpg_olap.duckdb │
          └──────────────────┘
```

**How it works:**
1. **Chatbot (Flask)** - Users ask natural language questions
2. **Metabase** - Users explore data visually with charts/dashboards
3. **Both** connect to the same DuckDB database
4. **Seamless experience** - "Ask questions" + "See dashboards"

---

## Next Steps

1. ✅ Start Metabase: `start_metabase.bat`
2. ✅ Create admin account at http://localhost:3000
3. ✅ Connect to CPG Analytics database
4. ✅ Create your first dashboard
5. ✅ Embed dashboards in Flask app
6. 🎉 Show to business users!

---

## Support & Resources

- **Metabase Docs:** https://www.metabase.com/docs/
- **Video Tutorials:** https://www.metabase.com/learn/
- **Community Forum:** https://discourse.metabase.com/
- **Sample Dashboards:** https://www.metabase.com/learn/dashboards

---

## Summary

**What you get:**
- ✅ Tableau-quality dashboards
- ✅ Drag-and-drop chart builder
- ✅ SQL query interface
- ✅ Interactive filters and drill-downs
- ✅ Beautiful visualizations
- ✅ Embeddable in Flask app
- ✅ Free, open source
- ✅ Runs locally

**Time to value:** ~15 minutes from start to first dashboard

**Business user feedback:** "This looks just like Tableau!" 🎉
