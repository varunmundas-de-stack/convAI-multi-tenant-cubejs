# 🚀 SETUP GUIDE - CPG Conversational AI

**Complete Setup & Deployment Guide for Windows**

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Testing](#testing)
5. [Troubleshooting](#troubleshooting)
6. [Production Deployment](#production-deployment)

---

## ✅ Prerequisites

### **Required Software**

| Software | Version | Download Link |
|----------|---------|---------------|
| **Python** | 3.10+ | https://www.python.org/downloads/ |
| **Git** | Latest | https://git-scm.com/downloads |
| **Web Browser** | Latest Chrome/Firefox | - |

### **System Requirements**

- **OS:** Windows 10/11
- **RAM:** 2GB minimum (4GB recommended)
- **Disk:** 500MB free space
- **Network:** Internet (for package installation)

---

## ⚡ Quick Start (5 Minutes)

**For experienced users who want to get running immediately:**

```bash
# 1. Clone repository
cd D:\
git clone https://github.com/varunmundas-de-stack/Conve-AI-Project-RelDB-Only.git
cd Conve-AI-Project-RelDB-Only

# 2. Install dependencies
pip install duckdb ollama pydantic pyyaml rich python-dateutil flask flask-login werkzeug bcrypt

# 3. Create databases
python database/create_user_db.py
python database/create_multi_schema_demo.py

# 4. Start server
python frontend/app_with_auth.py

# 5. Open browser
# http://localhost:5000
# Login: nestle_analyst / nestle123
```

**Done!** 🎉

---

## 📦 Detailed Setup

### **Step 1: Install Python**

1. Download Python 3.12 from https://www.python.org/downloads/
2. **IMPORTANT:** Check "Add Python to PATH" during installation
3. Verify installation:
   ```bash
   python --version
   # Should show: Python 3.12.x
   ```

---

### **Step 2: Clone Repository**

**Option A: Using Git (Recommended)**
```bash
cd D:\
git clone https://github.com/varunmundas-de-stack/Conve-AI-Project-RelDB-Only.git
cd Conve-AI-Project-RelDB-Only
```

**Option B: Download ZIP**
1. Go to: https://github.com/varunmundas-de-stack/Conve-AI-Project-RelDB-Only
2. Click "Code" → "Download ZIP"
3. Extract to `D:\Conve-AI-Project-RelDB-Only`
4. Open PowerShell/CMD in that folder

---

### **Step 3: Install Python Packages**

**Method 1: Individual Installation (Recommended)**
```bash
pip install duckdb ollama pydantic pyyaml rich python-dateutil flask flask-login werkzeug bcrypt
```

**Expected Output:**
```
Successfully installed duckdb-1.4.4 flask-3.1.2 flask-login-0.6.3
bcrypt-5.0.0 werkzeug-3.1.5 ollama-0.6.1 pydantic-2.12.5 ...
(Total: ~28 packages)
```

**Method 2: Using requirements.txt (Alternative)**
```bash
pip install -r requirements.txt
```

**Verification:**
```bash
pip list
# Should show all installed packages
```

---

### **Step 4: Create Databases**

#### **A. User Authentication Database**

```bash
python database/create_user_db.py
```

**Expected Output:**
```
Creating user database for RBAC...
[OK] User database created successfully!

======================================================================
SAMPLE USERS CREATED
======================================================================
Username             Password        Client          Role
======================================================================
nestle_analyst       nestle123       nestle          analyst
unilever_analyst     unilever123     unilever        analyst
itc_analyst          itc123          itc             analyst
======================================================================

[OK] Database created at: D:\...\database\users.db
[OK] File size: 32.00 KB
```

**What it created:**
- ✅ `database/users.db` (32 KB)
- ✅ 3 users (one per client)
- ✅ 3 client configurations
- ✅ Audit log table

---

#### **B. Multi-Tenant Analytics Database**

```bash
python database/create_multi_schema_demo.py
```

**Expected Output:**
```
Creating multi-schema DuckDB database...

[*] Creating schema: client_nestle
[OK] Schema client_nestle created with sample data

[*] Creating schema: client_unilever
[OK] Schema client_unilever created with sample data

[*] Creating schema: client_itc
[OK] Schema client_itc created with sample data

[OK] Multi-tenant database created at: D:\...\database\cpg_multi_tenant.duckdb
[OK] File size: 9740.00 KB

[OK] Setup complete! Each client has isolated data.
```

**What it created:**
- ✅ `database/cpg_multi_tenant.duckdb` (~10 MB)
- ✅ 3 isolated schemas (client_nestle, client_unilever, client_itc)
- ✅ 6 tables per schema (1 fact + 5 dimensions)
- ✅ 50 sample transactions per client (150 total)

---

### **Step 5: Verify Setup**

**Check files exist:**
```bash
dir database\*.db
dir database\*.duckdb
```

**Expected:**
```
users.db                    32 KB
cpg_multi_tenant.duckdb     9.7 MB
```

**Check database contents:**
```bash
python -c "import sqlite3; conn = sqlite3.connect('database/users.db'); print('Users:', conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]); conn.close()"
```

**Expected:** `Users: 3`

---

### **Step 6: Start Flask Server**

```bash
python frontend/app_with_auth.py
```

**Expected Output:**
```
============================================================
CPG Conversational AI Chatbot (RBAC Enabled)
============================================================
Starting Flask server...
Open your browser and go to: http://localhost:5000
Login with one of the sample users:
  - nestle_analyst / nestle123
  - unilever_analyst / unilever123
  - itc_analyst / itc123
Press Ctrl+C to stop the server
============================================================
 * Running on http://0.0.0.0:5000
```

**Leave this terminal open!**

---

### **Step 7: Access Web Interface**

1. Open **Chrome** or **Firefox**
2. Navigate to: **http://localhost:5000**
3. You should see the login screen

---

## 🧪 Testing

### **Test 1: Login & Basic Query**

**Steps:**
1. Login with: `nestle_analyst` / `nestle123`
2. Should see:
   - Header: "Nestle Analyst" at top
   - Company: "Nestlé India"
   - Role: "analyst" badge
   - Logout button (top-right)
3. Click suggestion chip: **"Show top 5 brands by sales"**
4. Should see table with brands ending in "-nestle":
   ```
   Brand-B-nestle    377,845.26
   Brand-D-nestle    364,520.18
   Brand-A-nestle    352,110.45
   ...
   ```

**✅ PASS if:** You see Nestle brands only

---

### **Test 2: Schema Isolation**

**Steps:**
1. Logout (click logout button)
2. Login with: `unilever_analyst` / `unilever123`
3. Click: **"Show top 5 brands by sales"**
4. Should see DIFFERENT brands ending in "-unilever":
   ```
   Brand-A-unilever    425,680.90
   Brand-C-unilever    398,520.45
   Brand-B-unilever    385,210.30
   ...
   ```

**✅ PASS if:** Unilever brands are DIFFERENT from Nestle brands

---

### **Test 3: Permission Denied (Cross-Client)**

**Steps:**
1. Login as: `nestle_analyst`
2. Type: **"Show Unilever top brands"**
3. Should see permission denied message:
   ```
   🚫 Permission Denied
   You do not have access to data from: Unilever
   ```

**✅ PASS if:** Permission denied message appears

---

### **Test 4: Out-of-Scope Question**

**Steps:**
1. Type: **"What is the weather today?"**
2. Should see out-of-scope message:
   ```
   ⚠️ Out of Scope Question
   This chatbot is specialized for CPG sales analytics only.
   ```

**✅ PASS if:** Out-of-scope message appears

---

### **Test 5: Metadata Question Blocking**

**Steps:**
1. Type: **"What tables are in the database?"**
2. Should see metadata blocking message:
   ```
   ❌ Out of Scope Question
   This chatbot is for analytics queries only,
   not database metadata exploration.
   ```

**✅ PASS if:** Metadata message appears

---

### **Test 6: All Query Types**

**Try these queries (as any user):**

| Query | Expected Result |
|-------|----------------|
| `Show top 5 brands by sales` | Table with 5 brands |
| `Weekly sales trend for last 6 weeks` | Table with 6 weeks |
| `Total sales this month` | Single number |
| `Compare sales by channel` | Table with channels |
| `Top 10 SKUs by volume` | Table with 10 SKUs |

**✅ PASS if:** All queries return results

---

### **Test 7: Session Expiry**

**Steps:**
1. Login and use app
2. Close browser completely
3. Reopen browser
4. Go to: http://localhost:5000
5. Should show login screen (not auto-login)

**✅ PASS if:** Login screen appears

---

## 🔧 Troubleshooting

### **Issue 1: "python: command not found"**

**Cause:** Python not in PATH

**Fix:**
```bash
# Find Python installation
where python

# If not found, reinstall Python with "Add to PATH" checked
```

---

### **Issue 2: "Module not found" errors**

**Cause:** Packages not installed

**Fix:**
```bash
# Reinstall all packages
pip install --force-reinstall duckdb flask flask-login werkzeug bcrypt ollama pydantic pyyaml rich python-dateutil
```

---

### **Issue 3: "Address already in use (Port 5000)"**

**Cause:** Another app using port 5000

**Fix Option A - Kill process:**
```bash
# Find process
netstat -ano | findstr :5000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

**Fix Option B - Use different port:**
```python
# Edit frontend/app_with_auth.py, last line:
app.run(debug=True, host='0.0.0.0', port=5001)  # Change to 5001
```

---

### **Issue 4: "undefined" error in chat**

**Cause:** Server error not displayed properly

**Fix:**
```bash
# Check server terminal for Python errors
# Press F12 in browser → Console tab → Check for JavaScript errors
```

**Common causes:**
- Database file missing
- YAML config file missing
- Python package import error

---

### **Issue 5: Shows old login after restart**

**Cause:** Browser session cookie persists

**Fix:**
```bash
# Clear browser cookies
# Chrome: Ctrl + Shift + Delete → Clear cookies

# OR use Incognito mode
# Chrome: Ctrl + Shift + N
```

---

### **Issue 6: "Cannot find table" SQL errors**

**Cause:** Database schemas not created properly

**Fix:**
```bash
# Delete old databases
del database\users.db
del database\cpg_multi_tenant.duckdb

# Recreate
python database\create_user_db.py
python database\create_multi_schema_demo.py
```

---

### **Issue 7: Slow performance**

**Checks:**
```bash
# Check file sizes
dir database\*.db*

# Should be:
# users.db: 32 KB
# cpg_multi_tenant.duckdb: ~10 MB

# If much larger, regenerate databases
```

---

## 🚀 Production Deployment

### **Option 1: Windows Server with Gunicorn**

**Not Recommended** - Gunicorn doesn't support Windows

---

### **Option 2: Windows Server with Waitress**

**Install Waitress:**
```bash
pip install waitress
```

**Create production script** `production_server.py`:
```python
from waitress import serve
from frontend.app_with_auth import app

print("Starting production server on port 8080...")
serve(app, host='0.0.0.0', port=8080, threads=4)
```

**Run:**
```bash
python production_server.py
```

---

### **Option 3: Linux Server with Gunicorn + NGINX**

**Install:**
```bash
pip install gunicorn

sudo apt install nginx
```

**Gunicorn systemd service** `/etc/systemd/system/cpg-chatbot.service`:
```ini
[Unit]
Description=CPG Chatbot
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/cpg-chatbot
ExecStart=/usr/bin/gunicorn -w 4 -b 127.0.0.1:5000 frontend.app_with_auth:app
Restart=always

[Install]
WantedBy=multi-user.target
```

**NGINX config** `/etc/nginx/sites-available/cpg-chatbot`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Start services:**
```bash
sudo systemctl start cpg-chatbot
sudo systemctl enable cpg-chatbot
sudo systemctl restart nginx
```

---

### **Option 4: Docker Container**

**Create** `Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir duckdb flask flask-login werkzeug bcrypt ollama pydantic pyyaml rich python-dateutil

# Create databases
RUN python database/create_user_db.py && \
    python database/create_multi_schema_demo.py

EXPOSE 5000

CMD ["python", "frontend/app_with_auth.py"]
```

**Build and run:**
```bash
docker build -t cpg-chatbot .
docker run -d -p 5000:5000 cpg-chatbot
```

---

## 📊 User Management

### **Add New User**

```bash
python database/add_user.py
```

Follow prompts to add user.

---

### **Reset User Password**

```python
# reset_password.py
import sqlite3
import bcrypt

username = "nestle_analyst"
new_password = "newpassword123"

# Hash password
salt = bcrypt.gensalt()
password_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')

# Update database
conn = sqlite3.connect('database/users.db')
conn.execute('UPDATE users SET password_hash = ? WHERE username = ?',
             (password_hash, username))
conn.commit()
conn.close()

print(f"Password reset for {username}")
```

---

### **Add New Client**

**1. Create YAML config:**
```bash
cp semantic_layer/configs/client_nestle.yaml semantic_layer/configs/client_newclient.yaml
```

**2. Edit config:**
- Change `client.id` to `newclient`
- Change `client.name` to "New Client Name"
- Change `database.schema` to `client_newclient`

**3. Create schema in DuckDB:**
```python
import duckdb
conn = duckdb.connect('database/cpg_multi_tenant.duckdb')
conn.execute('CREATE SCHEMA client_newclient')
# Create tables...
conn.close()
```

**4. Add client record to users.db:**
```python
import sqlite3
conn = sqlite3.connect('database/users.db')
conn.execute('''
    INSERT INTO clients (client_id, client_name, database_path, config_path, schema_name)
    VALUES (?, ?, ?, ?, ?)
''', ('newclient', 'New Client Name', 'database/cpg_multi_tenant.duckdb',
      'semantic_layer/configs/client_newclient.yaml', 'client_newclient'))
conn.commit()
conn.close()
```

**5. Add user for new client**

---

## 🎯 Next Steps

### **After Setup:**

1. ✅ **Customize YAML configs** for your metrics
2. ✅ **Load real data** into database
3. ✅ **Change Flask secret key** in production
4. ✅ **Set up HTTPS** for production
5. ✅ **Configure backup** for database files
6. ✅ **Set up monitoring** (logs, alerts)

---

## 📚 Additional Resources

- **Architecture Details:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Quick Reference:** [README.md](README.md)
- **GitHub Repository:** https://github.com/varunmundas-de-stack/Conve-AI-Project-RelDB-Only

---

## ✅ Setup Checklist

Before going live, verify:

- [ ] Python 3.10+ installed
- [ ] All packages installed (28 packages)
- [ ] Database files created (users.db + cpg_multi_tenant.duckdb)
- [ ] Flask server starts without errors
- [ ] Can login with all 3 users
- [ ] Schema isolation working (different data per client)
- [ ] Permission denied for cross-client queries
- [ ] Out-of-scope questions blocked
- [ ] Session expires on browser close
- [ ] Audit log recording queries

**If all checked:** Ready for use! 🎉

---

**Need help? Check [ARCHITECTURE.md](ARCHITECTURE.md) for system details.**
