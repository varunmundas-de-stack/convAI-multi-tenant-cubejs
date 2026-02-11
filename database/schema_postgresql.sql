-- PostgreSQL Schema for Tenant Analytics
-- Compatible with the existing DuckDB schema structure

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Dimension: Date
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    week INTEGER,
    day INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR(20),
    is_weekend BOOLEAN DEFAULT FALSE,
    is_holiday BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_dim_date_date ON dim_date(date);
CREATE INDEX idx_dim_date_year_month ON dim_date(year, month);

-- Dimension: Customer
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key INTEGER PRIMARY KEY,
    customer_id VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    age INTEGER,
    gender VARCHAR(20),
    occupation VARCHAR(100),
    income_bracket VARCHAR(50),
    credit_score INTEGER,
    customer_segment VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    account_open_date DATE,
    customer_status VARCHAR(20) DEFAULT 'Active'
);

CREATE INDEX idx_dim_customer_segment ON dim_customer(customer_segment);
CREATE INDEX idx_dim_customer_state ON dim_customer(state);
CREATE INDEX idx_dim_customer_status ON dim_customer(customer_status);

-- Dimension: Account
CREATE TABLE IF NOT EXISTS dim_account (
    account_key INTEGER PRIMARY KEY,
    account_id VARCHAR(50) UNIQUE NOT NULL,
    account_type VARCHAR(50),
    account_subtype VARCHAR(50),
    interest_rate DECIMAL(5,2),
    account_status VARCHAR(20) DEFAULT 'Active',
    branch_id VARCHAR(50),
    branch_name VARCHAR(100),
    region VARCHAR(100)
);

CREATE INDEX idx_dim_account_type ON dim_account(account_type);
CREATE INDEX idx_dim_account_region ON dim_account(region);

-- Dimension: Product
CREATE TABLE IF NOT EXISTS dim_product (
    product_key INTEGER PRIMARY KEY,
    product_id VARCHAR(50) UNIQUE NOT NULL,
    product_name VARCHAR(200),
    product_category VARCHAR(100),
    product_type VARCHAR(100),
    sub_category VARCHAR(100),  -- New field
    risk_level VARCHAR(20),
    unit_weight DECIMAL(10,2),   -- New field (kg)
    unit_volume DECIMAL(10,2),   -- New field (liters)
    unit_of_measure VARCHAR(20)  -- New field
);

CREATE INDEX idx_dim_product_category ON dim_product(product_category);
CREATE INDEX idx_dim_product_type ON dim_product(product_type);
CREATE INDEX idx_dim_product_subcategory ON dim_product(sub_category);

-- Dimension: Transaction Type
CREATE TABLE IF NOT EXISTS dim_transaction_type (
    transaction_type_key INTEGER PRIMARY KEY,
    transaction_type VARCHAR(50) NOT NULL,
    transaction_category VARCHAR(50),
    is_credit BOOLEAN DEFAULT FALSE,
    is_debit BOOLEAN DEFAULT FALSE
);

-- Dimension: Sales Hierarchy (New)
CREATE TABLE IF NOT EXISTS dim_sales_hierarchy (
    hierarchy_key INTEGER PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    user_name VARCHAR(200),
    role_level VARCHAR(20), -- SO, ASM, ZSM, NSM
    reports_to VARCHAR(50),  -- Parent user_id
    city VARCHAR(100),
    state VARCHAR(100),
    zone VARCHAR(100),
    region VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sales_hier_role ON dim_sales_hierarchy(role_level);
CREATE INDEX idx_sales_hier_zone ON dim_sales_hierarchy(zone);
CREATE INDEX idx_sales_hier_state ON dim_sales_hierarchy(state);

-- Fact: Transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_key BIGSERIAL PRIMARY KEY,
    date_key INTEGER REFERENCES dim_date(date_key),
    customer_key INTEGER REFERENCES dim_customer(customer_key),
    account_key INTEGER REFERENCES dim_account(account_key),
    transaction_type_key INTEGER REFERENCES dim_transaction_type(transaction_type_key),
    transaction_amount DECIMAL(15,2),
    balance_after_transaction DECIMAL(15,2),
    transaction_fee DECIMAL(10,2),
    transaction_status VARCHAR(20),
    channel VARCHAR(50)
);

CREATE INDEX idx_fact_trans_date ON fact_transactions(date_key);
CREATE INDEX idx_fact_trans_customer ON fact_transactions(customer_key);
CREATE INDEX idx_fact_trans_account ON fact_transactions(account_key);

-- Fact: Loans
CREATE TABLE IF NOT EXISTS fact_loans (
    loan_key BIGSERIAL PRIMARY KEY,
    date_key INTEGER REFERENCES dim_date(date_key),
    customer_key INTEGER REFERENCES dim_customer(customer_key),
    product_key INTEGER REFERENCES dim_product(product_key),
    loan_amount DECIMAL(15,2),
    outstanding_balance DECIMAL(15,2),
    principal_paid DECIMAL(15,2),
    interest_paid DECIMAL(15,2),
    loan_status VARCHAR(20),
    default_flag BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_fact_loans_date ON fact_loans(date_key);
CREATE INDEX idx_fact_loans_customer ON fact_loans(customer_key);

-- Fact: Primary Sales (New - Company to Distributor)
CREATE TABLE IF NOT EXISTS fact_primary_sales (
    primary_sale_key BIGSERIAL PRIMARY KEY,
    date_key INTEGER REFERENCES dim_date(date_key),
    product_key INTEGER REFERENCES dim_product(product_key),
    seller_warehouse_code VARCHAR(50),
    seller_warehouse_name VARCHAR(200),
    distributor_id VARCHAR(50),
    distributor_name VARCHAR(200),
    quantity DECIMAL(15,2),
    billed_weight DECIMAL(15,2),  -- Calculated from product weight
    billed_volume DECIMAL(15,2),  -- Calculated from product volume
    unit_price DECIMAL(10,2),
    total_amount DECIMAL(15,2),
    discount_amount DECIMAL(10,2),
    net_amount DECIMAL(15,2),
    sales_person_id VARCHAR(50),  -- Links to dim_sales_hierarchy
    region VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_primary_sales_date ON fact_primary_sales(date_key);
CREATE INDEX idx_primary_sales_product ON fact_primary_sales(product_key);
CREATE INDEX idx_primary_sales_warehouse ON fact_primary_sales(seller_warehouse_code);
CREATE INDEX idx_primary_sales_person ON fact_primary_sales(sales_person_id);

-- Fact: Account Balances
CREATE TABLE IF NOT EXISTS fact_account_balances (
    balance_key BIGSERIAL PRIMARY KEY,
    date_key INTEGER REFERENCES dim_date(date_key),
    account_key INTEGER REFERENCES dim_account(account_key),
    opening_balance DECIMAL(15,2),
    closing_balance DECIMAL(15,2),
    average_balance DECIMAL(15,2)
);

CREATE INDEX idx_fact_balances_date ON fact_account_balances(date_key);
CREATE INDEX idx_fact_balances_account ON fact_account_balances(account_key);

-- Fact: Investments
CREATE TABLE IF NOT EXISTS fact_investments (
    investment_key BIGSERIAL PRIMARY KEY,
    date_key INTEGER REFERENCES dim_date(date_key),
    customer_key INTEGER REFERENCES dim_customer(customer_key),
    product_key INTEGER REFERENCES dim_product(product_key),
    investment_amount DECIMAL(15,2),
    current_value DECIMAL(15,2),
    return_amount DECIMAL(15,2)
);

CREATE INDEX idx_fact_invest_date ON fact_investments(date_key);
CREATE INDEX idx_fact_invest_customer ON fact_investments(customer_key);
