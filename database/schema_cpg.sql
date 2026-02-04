-- CPG/Sales OLAP Schema
-- Fact and Dimension tables for Consumer Packaged Goods Secondary Sales Analytics

-- Dimension: Date (with CPG-specific attributes)
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name VARCHAR,
    week INTEGER,
    day INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    fiscal_month INTEGER,
    fiscal_week INTEGER,
    is_promotional_week BOOLEAN,
    season VARCHAR,  -- Q1: Winter, Q2: Spring, Q3: Summer, Q4: Fall
    week_of_month INTEGER
);

-- Dimension: Product (Manufacturer → Division → Category → Brand → SKU)
CREATE TABLE dim_product (
    product_key INTEGER PRIMARY KEY,
    sku_code VARCHAR,
    sku_name VARCHAR,
    brand_name VARCHAR,
    brand_code VARCHAR,
    category_name VARCHAR,
    category_code VARCHAR,
    division_name VARCHAR,
    manufacturer_name VARCHAR,
    pack_size VARCHAR,
    pack_size_value DECIMAL(10,2),
    pack_size_unit VARCHAR,  -- ml, gm, pieces
    mrp DECIMAL(10,2),
    product_status VARCHAR,  -- Active, Discontinued, Seasonal
    launch_date DATE,
    is_focus_brand BOOLEAN,
    hsn_code VARCHAR
);

-- Dimension: Geography (Zone → State → District → Town → Outlet)
CREATE TABLE dim_geography (
    geography_key INTEGER PRIMARY KEY,
    outlet_code VARCHAR,
    outlet_name VARCHAR,
    town_code VARCHAR,
    town_name VARCHAR,
    district_code VARCHAR,
    district_name VARCHAR,
    state_code VARCHAR,
    state_name VARCHAR,
    zone_code VARCHAR,
    zone_name VARCHAR,
    region_code VARCHAR,
    region_name VARCHAR,
    outlet_classification VARCHAR,  -- A, B, C
    population_tier VARCHAR,  -- Tier-1, Tier-2, Tier-3
    urban_rural VARCHAR
);

-- Dimension: Customer (Distributor → Retailer → Outlet Type)
CREATE TABLE dim_customer (
    customer_key INTEGER PRIMARY KEY,
    distributor_code VARCHAR,
    distributor_name VARCHAR,
    retailer_code VARCHAR,
    retailer_name VARCHAR,
    outlet_type VARCHAR,  -- Kirana, Supermarket, Hypermarket, Medical Store
    outlet_subtype VARCHAR,  -- Traditional, Modern, Institutional
    customer_segment VARCHAR,  -- Premium, Standard, Budget
    customer_status VARCHAR,  -- Active, Inactive, Suspended
    credit_limit DECIMAL(15,2),
    credit_days INTEGER,
    onboarding_date DATE,
    last_order_date DATE,
    gst_number VARCHAR,
    pan_number VARCHAR
);

-- Dimension: Channel
CREATE TABLE dim_channel (
    channel_key INTEGER PRIMARY KEY,
    channel_code VARCHAR,
    channel_name VARCHAR,  -- GT, MT, E-Com, IWS, Pharma
    channel_category VARCHAR,  -- Direct, Indirect
    channel_description VARCHAR
);

-- Fact: Secondary Sales (Distributor to Retailer)
CREATE TABLE fact_secondary_sales (
    sales_key INTEGER PRIMARY KEY,
    date_key INTEGER,
    product_key INTEGER,
    geography_key INTEGER,
    customer_key INTEGER,
    channel_key INTEGER,
    invoice_number VARCHAR,
    invoice_date DATE,
    invoice_value DECIMAL(15,2),
    invoice_quantity INTEGER,
    base_price DECIMAL(10,2),
    discount_amount DECIMAL(15,2),
    discount_percentage DECIMAL(5,2),
    tax_amount DECIMAL(15,2),
    net_value DECIMAL(15,2),
    margin_amount DECIMAL(15,2),
    margin_percentage DECIMAL(5,2),
    return_flag BOOLEAN,
    return_amount DECIMAL(15,2),
    sales_rep_code VARCHAR,
    sales_type VARCHAR,  -- Regular, Promotional, Sample
    payment_terms VARCHAR,  -- Cash, Credit
    payment_status VARCHAR,  -- Paid, Pending, Overdue
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
    FOREIGN KEY (geography_key) REFERENCES dim_geography(geography_key),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    FOREIGN KEY (channel_key) REFERENCES dim_channel(channel_key)
);

-- Fact: Primary Sales (Manufacturer to Distributor)
CREATE TABLE fact_primary_sales (
    primary_sales_key INTEGER PRIMARY KEY,
    date_key INTEGER,
    product_key INTEGER,
    customer_key INTEGER,
    channel_key INTEGER,
    order_number VARCHAR,
    order_date DATE,
    order_quantity INTEGER,
    order_value DECIMAL(15,2),
    dispatch_quantity INTEGER,
    dispatch_value DECIMAL(15,2),
    pending_quantity INTEGER,
    freight_cost DECIMAL(15,2),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    FOREIGN KEY (channel_key) REFERENCES dim_channel(channel_key)
);

-- Fact: Inventory (Stock Levels)
CREATE TABLE fact_inventory (
    inventory_key INTEGER PRIMARY KEY,
    date_key INTEGER,
    product_key INTEGER,
    geography_key INTEGER,
    customer_key INTEGER,
    opening_stock INTEGER,
    closing_stock INTEGER,
    receipts INTEGER,
    issues INTEGER,
    stock_value DECIMAL(15,2),
    days_of_supply DECIMAL(5,1),
    reorder_level INTEGER,
    max_stock_level INTEGER,
    stock_status VARCHAR,  -- Normal, Below Reorder, Overstock, Out of Stock
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
    FOREIGN KEY (geography_key) REFERENCES dim_geography(geography_key),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key)
);

-- Fact: Distribution Metrics
CREATE TABLE fact_distribution (
    distribution_key INTEGER PRIMARY KEY,
    date_key INTEGER,
    product_key INTEGER,
    geography_key INTEGER,
    channel_key INTEGER,
    total_outlets INTEGER,
    outlets_with_stock INTEGER,
    outlets_with_sales INTEGER,
    numeric_distribution DECIMAL(5,2),  -- % of outlets with product
    weighted_distribution DECIMAL(5,2),  -- % weighted by outlet sales
    share_of_shelf DECIMAL(5,2),
    out_of_stock_outlets INTEGER,
    average_facing_count DECIMAL(5,2),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
    FOREIGN KEY (geography_key) REFERENCES dim_geography(geography_key),
    FOREIGN KEY (channel_key) REFERENCES dim_channel(channel_key)
);

-- Create indexes for performance
CREATE INDEX idx_secondary_sales_date ON fact_secondary_sales(date_key);
CREATE INDEX idx_secondary_sales_product ON fact_secondary_sales(product_key);
CREATE INDEX idx_secondary_sales_geography ON fact_secondary_sales(geography_key);
CREATE INDEX idx_secondary_sales_customer ON fact_secondary_sales(customer_key);
CREATE INDEX idx_secondary_sales_channel ON fact_secondary_sales(channel_key);
CREATE INDEX idx_secondary_sales_invoice_date ON fact_secondary_sales(invoice_date);

CREATE INDEX idx_primary_sales_date ON fact_primary_sales(date_key);
CREATE INDEX idx_primary_sales_product ON fact_primary_sales(product_key);

CREATE INDEX idx_inventory_date ON fact_inventory(date_key);
CREATE INDEX idx_inventory_product ON fact_inventory(product_key);

CREATE INDEX idx_distribution_date ON fact_distribution(date_key);
CREATE INDEX idx_distribution_product ON fact_distribution(product_key);
