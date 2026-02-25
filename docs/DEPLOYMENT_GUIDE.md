# CPG Conversational AI — Deployment Guide

> End-to-end setup guide for running the platform locally (Docker) or on AWS.
> Covers system requirements, installation, data setup, Cube.js configuration, and starting the app.

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Software Prerequisites](#2-software-prerequisites)
3. [Clone the Repository](#3-clone-the-repository)
4. [Environment Variables](#4-environment-variables)
5. [Docker Deployment (Recommended)](#5-docker-deployment-recommended)
6. [Manual / Dev Deployment](#6-manual--dev-deployment)
7. [Login Credentials](#7-login-credentials)
8. [Architecture Overview](#8-architecture-overview)
9. [Cube.js Semantic Layer](#9-cubejs-semantic-layer)
10. [Sharing the App (ngrok / LAN)](#10-sharing-the-app-ngrok--lan)
11. [AWS Cloud Deployment](#11-aws-cloud-deployment)
12. [Windows Firewall & Ports](#12-windows-firewall--ports)
13. [Troubleshooting](#13-troubleshooting)
14. [Directory Structure](#14-directory-structure)
15. [Quick-Start Checklist](#15-quick-start-checklist)

---

## 1. System Requirements

### Docker (recommended path)

| Component | Minimum | Recommended |
|---|---|---|
| **OS** | Windows 11 / macOS 13+ / Ubuntu 22.04 | Windows 11 Pro / macOS 14+ |
| **CPU** | 4-core x64 | 8-core x64 |
| **RAM** | 8 GB | 16 GB |
| **Disk (free)** | 15 GB | 25 GB |
| **Network** | Setup only (model download ~2 GB) | — |

### LLM option — Claude API (lighter, needs internet)

| Component | Minimum |
|---|---|
| **RAM** | 4 GB |
| **Disk (free)** | 5 GB |
| **Network** | Always-on internet |
| **Anthropic API key** | Required — get one at https://console.anthropic.com |

> Claude API gives better query accuracy and requires no local model download.

---

## 2. Software Prerequisites

### 2.1 Docker Desktop

**Download:** https://www.docker.com/products/docker-desktop

Install and start Docker Desktop. Verify:
```powershell
docker --version
docker compose version
```
Expected: Docker 24+ and Compose v2+.

> Docker handles Python, Node.js, Ollama, and Cube.js automatically — no manual installs needed for the standard deployment path.

---

### 2.2 Git

**Download:** https://git-scm.com/download/win — use all default options.

```powershell
git --version
```

> If you received the project as a ZIP, skip Git — extract and go to Section 4.

---

### 2.3 Python 3.11+ (dev mode only)

Only needed if running Flask outside Docker. Skip for standard Docker deployment.

**Download:** https://www.python.org/downloads/windows/ — choose Python 3.13.x (64-bit).
During installation check **"Add Python to PATH"**.

---

## 3. Clone the Repository

```powershell
git clone https://github.com/varunmundas-de-stack/convAI-multi-tenant-cubejs.git
cd convAI-multi-tenant-cubejs
```

After cloning, confirm these folders exist:
```
cubejs\          ← Cube.js semantic layer service (NEW)
frontend\
frontend_react\
database\
semantic_layer\
security\
llm\
insights\
query_engine\
docs\
aws-deploy\
```

---

## 4. Environment Variables

### 4.1 Create your `.env` file

```powershell
copy .env.example .env
```

Open `.env` — the defaults work for local development. For production, change the secrets:

```env
# Flask
FLASK_SECRET_KEY=your-long-random-flask-secret

# LLM — false = local Ollama, true = Claude API
USE_CLAUDE_API=false
ANTHROPIC_API_KEY=          # only needed when USE_CLAUDE_API=true
ANONYMIZE_SCHEMA=false

# Cube.js — shared secret between Flask (JWT signer) and Cube.js (JWT verifier)
# Must be 32+ characters. Change this in production.
CUBEJS_API_SECRET=cpg-sales-assistant-cubejs-secret-2026

# Cube.js URL (internal Docker hostname — do not change for Docker Compose)
CUBEJS_URL=http://cubejs:4000

# Node environment for Cube.js container
NODE_ENV=development
```

> **Important:** `CUBEJS_API_SECRET` must be identical in both Flask and Cube.js — they share the same `.env` file via Docker Compose so this is automatic.

---

## 5. Docker Deployment (Recommended)

This is the standard path for testers, designers, and demo environments.
One command starts everything: Flask, Ollama (LLM), and Cube.js.

### 5.1 Build images (first time — ~5 minutes)

```powershell
docker compose build
```

What gets built:
- **app** — Python/Flask + React frontend (built inside Docker)
- **cubejs** — Cube.js server with DuckDB driver + jsonwebtoken

### 5.2 Start all services

```powershell
docker compose up
```

Wait until you see all three of these lines:
```
cpg_cubejs            | 🚀 Cube.js server is listening on 4000
cpg_sales_assistant   | Running on http://0.0.0.0:5000
cpg_ollama            | Listening on [::]:11434
```

> **First start:** Ollama downloads `llama3.2:3b` (~2 GB). This takes 3–5 minutes depending on your connection. Subsequent starts are instant.

### 5.3 Open in browser

```
http://localhost:5000
```

Login with `nestle_admin / admin123` (see [Section 7](#7-login-credentials)).

### 5.4 Stop everything

```powershell
Ctrl+C   # in the terminal running docker compose up
```
or from a separate terminal:
```powershell
docker compose down
```

### 5.5 Using Claude API instead of Ollama (optional)

In `.env`, set:
```env
USE_CLAUDE_API=true
ANTHROPIC_API_KEY=sk-ant-your-key-here
```
Then restart: `docker compose down && docker compose up`

---

## 6. Manual / Dev Deployment

Use this only if you're developing the Python/Flask code outside Docker.

### 6.1 Python environment

```powershell
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 6.2 Database initialisation (first time only)

```powershell
python database\create_user_db.py
python database\create_multi_schema_demo.py
```

### 6.3 Build the React frontend (first time only)

```powershell
cd frontend_react
npm install
npm run build
cd ..
```

### 6.4 Set environment variables

```powershell
$env:FLASK_SECRET_KEY = "dev-secret"
$env:CUBEJS_API_SECRET = "cpg-sales-assistant-cubejs-secret-2026"
$env:CUBEJS_URL = "http://localhost:4000"   # if Cube.js running locally
```

### 6.5 Start Ollama (if not using Claude API)

```powershell
ollama pull llama3.2:3b   # once
ollama serve               # keep this terminal open
```

### 6.6 Start Cube.js (optional — app falls back to legacy pipeline without it)

```powershell
cd cubejs
npm install
npm start
# runs on http://localhost:4000
cd ..
```

### 6.7 Start Flask

```powershell
venv\Scripts\activate
python frontend\app_with_auth.py
```

---

## 7. Login Credentials

All users are seeded by `database\create_user_db.py` (Docker runs this automatically).

### Standard users

| Username | Password | Tenant | Role |
|---|---|---|---|
| `nestle_admin` | `admin123` | Nestlé India | Admin — full data access |
| `nestle_analyst` | `analyst123` | Nestlé India | Analyst |
| `unilever_admin` | `admin123` | Unilever India | Admin |
| `unilever_analyst` | `analyst123` | Unilever India | Analyst |
| `itc_admin` | `admin123` | ITC Limited | Admin |
| `itc_analyst` | `analyst123` | ITC Limited | Analyst |

### Sales hierarchy users — Nestlé (Row-Level Security demo)

| Username | Password | Role | Data Scope |
|---|---|---|---|
| `nsm_rajesh` | `nsm123` | NSM | Full national view |
| `zsm_amit` | `zsm123` | ZSM | Zone North (ZSM01) only |
| `asm_rahul` | `asm123` | ASM | Area ZSM01_ASM1 only |
| `so_field1` | `so123` | SO | Territory ZSM01_ASM1_SO01 only |

> Row-Level Security is enforced at the Cube.js `queryRewrite` layer — each user sees only data within their assigned sales hierarchy scope.

---

## 8. Architecture Overview

```
Browser (React)
    ↓ login
Flask / Python  (port 5000)
    ├─ Authenticates user → issues Cube.js JWT
    ├─ Intent Parser (Ollama / Claude API) → SemanticQuery
    ├─ CubeJSAdapter → Cube.js query JSON
    └─ Calls Cube.js REST API with JWT
              ↓
Cube.js  (port 4000, Node.js)
    ├─ Validates JWT → extracts security context
    ├─ queryRewrite → injects RLS filter (SO/ASM/ZSM)
    ├─ Selects DuckDB schema (client_nestle / client_unilever / client_itc)
    ├─ Generates SQL
    └─ Executes against DuckDB
              ↓
Flask formats result → Browser
```

**Query path:**
1. User types question → Flask parses NL intent
2. Flask calls Cube.js REST `/cubejs-api/v1/load` with JWT
3. Cube.js runs RLS-filtered SQL against DuckDB
4. Flask formats result as HTML table / chart data
5. React renders response

**Fallback:** If Cube.js is unreachable, Flask automatically falls back to the legacy AST SQL pipeline — queries always return data.

---

## 9. Cube.js Semantic Layer

Cube.js is the query engine introduced in this version. It replaces the custom AST SQL builder for all non-diagnostic queries.

### What Cube.js does

| Responsibility | Implementation |
|---|---|
| Multi-tenant schema switching | `contextToAppId` + `COMPILE_CONTEXT.securityContext.clientId` |
| JWT authentication | `checkAuth` validates Flask-issued tokens |
| Row-level security | `queryRewrite` injects hierarchy code filter |
| SQL generation | Cube.js schema files → DuckDB SQL |
| Query execution | DuckDB driver (`@cubejs-backend/duckdb-driver`) |

### Schema files

Located in `cubejs/schema/`:

| File | Purpose |
|---|---|
| `FactSecondarySales.js` | Main fact table — 6 measures, 6 joins |
| `DimProduct.js` | Brand, category, SKU hierarchy |
| `DimGeography.js` | State, district, town hierarchy |
| `DimCustomer.js` | Distributor, retailer, outlet type |
| `DimChannel.js` | Sales channel |
| `DimDate.js` | Year, quarter, month, week grains |
| `DimSalesHierarchy.js` | SO → ASM → ZSM → NSM codes (used for RLS) |

### Measures available

| Metric | Cube.js member |
|---|---|
| Secondary Sales Value | `FactSecondarySales.secondary_sales_value` |
| Secondary Sales Volume | `FactSecondarySales.secondary_sales_volume` |
| Gross Sales Value | `FactSecondarySales.gross_sales_value` |
| Discount Amount | `FactSecondarySales.discount_amount` |
| Margin Amount | `FactSecondarySales.margin_amount` |
| Invoice Count | `FactSecondarySales.invoice_count` |

### Verify Cube.js is running

From a browser or terminal (after `docker compose up`):
```
http://localhost:4000/cubejs-api/v1/meta
```
Expected: `{"error":"Authorization header isn't set"}` — confirms Cube.js is up and auth is enforced.

---

## 10. Sharing the App (ngrok / LAN)

### Option A — ngrok (public URL, remote demos)

```powershell
# Install
winget install ngrok.ngrok

# Authenticate (one time)
ngrok config add-authtoken YOUR_TOKEN

# Start tunnel (app must be running on port 5000)
ngrok http 5000
```

Share the `https://xxxx.ngrok-free.app` URL with attendees.

> Free tier generates a new URL on each restart. Keep the ngrok terminal open.

### Option B — LAN IP (same Wi-Fi)

```powershell
ipconfig   # find IPv4 Address, e.g. 192.168.1.100
```

Share: `http://192.168.1.100:5000`

Allow port 5000 through Windows Firewall (see [Section 12](#12-windows-firewall--ports)).

---

## 11. AWS Cloud Deployment

All scripts are in `aws-deploy\`. See [`aws-deploy/README.md`](../aws-deploy/README.md) for full details.

**Quick summary:**
- Launch EC2 `t3.medium` (Ubuntu 22.04, 4 GB RAM minimum)
- Run `aws-deploy/setup.sh` on the instance
- Copy `.env` with production secrets (especially `CUBEJS_API_SECRET`)
- `docker compose up -d`
- App runs behind Nginx on port 80
- Estimated cost: ~$33/month

---

## 12. Windows Firewall & Ports

| Service | Port | When used |
|---|---|---|
| Flask app | **5000** | Always |
| Cube.js API | **4000** | Always (query engine) |
| Ollama LLM | **11434** | When `USE_CLAUDE_API=false` |

> Ports 4000 and 11434 are internal Docker ports — only port 5000 needs to be opened for LAN/external access.

### Allow port 5000 for LAN access

1. Start → **Windows Defender Firewall → Advanced Settings**
2. **Inbound Rules → New Rule → Port → TCP → 5000**
3. Allow the connection → name it `CPG Analytics App`

---

## 13. Troubleshooting

### Docker

**`docker compose up` — Cube.js exits immediately**
```powershell
docker compose logs cubejs
```
Common cause: `CUBEJS_API_SECRET` not set in `.env`. Check `.env` exists and has the key.

**`cpg_cubejs` starts but queries fall back to legacy pipeline**

Flask logs will show: `Cube.js error (...), falling back to legacy executor`

Check Cube.js logs for the root cause:
```powershell
docker compose logs cubejs --tail=50
```

**Ollama model download stuck**

First start downloads `llama3.2:3b` (~2 GB). Wait for:
```
cpg_ollama | pulling manifest
cpg_ollama | pulling ...done
```
If it hangs, restart: `docker compose restart ollama`

**Port 5000 already in use**
```powershell
netstat -ano | findstr :5000
taskkill /PID <pid> /F
```

### Manual / Dev mode

**`ModuleNotFoundError: No module named 'jwt'`**
```powershell
pip install PyJWT
```

**`ModuleNotFoundError: No module named 'flask_login'`**
```powershell
pip install -r requirements.txt
```

**`sqlite3.OperationalError: unable to open database file`**
```powershell
python database\create_user_db.py
python database\create_multi_schema_demo.py
```

**Login returns 500 error**

Virtual environment not active:
```powershell
venv\Scripts\activate
python frontend\app_with_auth.py
```

**React frontend blank page / 404**
```powershell
cd frontend_react
npm install
npm run build
cd ..
```

**Insights tab empty**

Wait 15–30 seconds — insights generate in a background thread on startup. Watch for `[Insights]` lines in the terminal.

---

## 14. Directory Structure

```
convAI-multi-tenant-cubejs\
│
├── cubejs\                          # ← NEW: Cube.js semantic layer service
│   ├── cube.js                      # Main config: JWT auth, RLS, DuckDB driver
│   ├── package.json                 # Node deps: @cubejs-backend/server, duckdb-driver, jsonwebtoken
│   ├── Dockerfile                   # Cube.js container build
│   ├── .env.example                 # Cube.js env vars template
│   └── schema\                      # Cube definitions (one per table)
│       ├── FactSecondarySales.js    # 6 measures + 6 joins
│       ├── DimProduct.js
│       ├── DimGeography.js
│       ├── DimCustomer.js
│       ├── DimChannel.js
│       ├── DimDate.js
│       └── DimSalesHierarchy.js    # SO/ASM/ZSM/NSM codes for RLS
│
├── frontend\                        # Flask web application
│   ├── app_with_auth.py             # Main app — RBAC, Cube.js integration, all API endpoints
│   └── static\react\                # Built React frontend (generated by npm run build)
│
├── frontend_react\                  # React source code (Vite + Tailwind)
│   ├── src\
│   │   ├── components\              # ChatTab, DashboardTab, InsightsTab, etc.
│   │   ├── pages\                   # LoginPage, DashboardPage
│   │   └── api\client.js            # API client (calls Flask endpoints)
│   ├── package.json
│   └── vite.config.js
│
├── semantic_layer\                  # NL → query translation
│   ├── cubejs_adapter.py            # ← NEW: SemanticQuery → Cube.js JSON + REST caller
│   ├── semantic_layer.py            # YAML config parser
│   ├── query_builder.py             # Legacy AST SQL builder (fallback)
│   ├── orchestrator.py              # Multi-query diagnostic workflow
│   ├── validator.py
│   └── configs\                     # Per-tenant YAML configs
│       ├── client_nestle.yaml
│       ├── client_unilever.yaml
│       └── client_itc.yaml
│
├── security\                        # Auth and access control
│   ├── cubejs_token.py              # ← NEW: JWT generator for Cube.js auth
│   ├── auth.py                      # Flask-Login user auth
│   ├── rls.py                       # Row-Level Security filters
│   └── audit.py                     # Query audit trail
│
├── database\                        # Database scripts and files
│   ├── create_user_db.py            # Creates users.db
│   ├── create_multi_schema_demo.py  # Creates cpg_multi_tenant.duckdb
│   ├── users.db                     # ← created on first run
│   └── cpg_multi_tenant.duckdb      # ← created on first run (11.5 MB)
│
├── llm\                             # LLM intent parsing
│   └── intent_parser_v2.py          # Ollama + Claude dual-provider parser
│
├── insights\
│   └── hierarchy_insights_engine.py # Proactive insights engine
│
├── query_engine\                    # Legacy SQL execution (fallback + diagnostics)
│   ├── executor.py
│   └── query_validator.py
│
├── aws-deploy\                      # AWS EC2 deployment scripts
│
├── docs\                            # Documentation
│   ├── DEPLOYMENT_GUIDE.md          # This file
│   └── ARCHITECTURE.md
│
├── .env.example                     # Environment variables template
├── .env                             # Your local config (git-ignored)
├── Dockerfile                       # Flask + React container build
├── docker-compose.yml               # Orchestrates app + ollama + cubejs
└── requirements.txt                 # Python dependencies
```

---

## 15. Quick-Start Checklist

Use this before handing off to a tester, designer, or running a demo.

### Docker path (standard)

- [ ] Docker Desktop installed and running
- [ ] Repo cloned from `https://github.com/varunmundas-de-stack/convAI-multi-tenant-cubejs`
- [ ] `.env` file created from `.env.example` (`copy .env.example .env`)
- [ ] `CUBEJS_API_SECRET` set in `.env` (32+ characters)
- [ ] `docker compose build` completed without errors
- [ ] `docker compose up` shows all 3 services started (app, ollama, cubejs)
- [ ] Browser opens `http://localhost:5000` — login page visible
- [ ] Login with `nestle_admin / admin123` succeeds
- [ ] Chat tab: `"show top 5 brands by sales"` returns a table
- [ ] Docker logs show `[Cube.js] Load Request` — confirms Cube.js is handling queries
- [ ] Insights tab loads (wait 15 sec on first start)
- [ ] Dashboard tab loads with KPI cards and charts
- [ ] Login as `so_field1 / so123` — same query returns fewer rows (RLS working)
- [ ] Login as `unilever_admin / admin123` — different brand names (tenant isolation working)

### Cube.js sanity check

Open in browser while app is running:
```
http://localhost:4000/cubejs-api/v1/meta
```
Expected response: `{"error":"Authorization header isn't set"}`
This confirms Cube.js is up and its JWT guard is active.

---

*Last updated: February 2026 — Cube.js semantic layer integration*
