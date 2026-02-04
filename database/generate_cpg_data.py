"""
Generate sample CPG/Sales data for the OLAP database
"""
import duckdb
import random
from datetime import datetime, timedelta
from pathlib import Path

# Configuration - MINIMAL for fast generation
NUM_SKUS = 50
NUM_BRANDS = 5
NUM_CATEGORIES = 3
NUM_DISTRIBUTORS = 20
NUM_RETAILERS = 100
NUM_OUTLETS = 200
NUM_ZONES = 4
NUM_STATES = 8
NUM_DISTRICTS = 20
NUM_TOWNS = 50
NUM_DAYS = 90  # Last 3 months
NUM_SECONDARY_SALES = 1000  # Minimal dataset

def generate_date_dimension(conn):
    """Generate date dimension for the last year with CPG-specific attributes"""
    print("Generating date dimension...")

    start_date = datetime.now() - timedelta(days=NUM_DAYS)
    dates = []

    for i in range(NUM_DAYS):
        current_date = start_date + timedelta(days=i)
        fiscal_year = current_date.year if current_date.month >= 4 else current_date.year - 1
        fiscal_quarter = ((current_date.month - 4) % 12) // 3 + 1
        fiscal_month = ((current_date.month - 4) % 12) + 1
        fiscal_week = ((i + start_date.weekday()) // 7) + 1

        # Season mapping
        season_map = {1: 'Winter', 2: 'Winter', 3: 'Spring', 4: 'Spring', 5: 'Spring',
                      6: 'Summer', 7: 'Summer', 8: 'Summer', 9: 'Fall', 10: 'Fall',
                      11: 'Fall', 12: 'Winter'}

        dates.append({
            'date_key': int(current_date.strftime('%Y%m%d')),
            'date': current_date.strftime('%Y-%m-%d'),
            'year': current_date.year,
            'quarter': (current_date.month - 1) // 3 + 1,
            'month': current_date.month,
            'month_name': current_date.strftime('%B'),
            'week': current_date.isocalendar()[1],
            'day': current_date.day,
            'day_of_week': current_date.weekday(),
            'day_name': current_date.strftime('%A'),
            'is_weekend': current_date.weekday() >= 5,
            'is_holiday': random.random() < 0.05,
            'fiscal_year': fiscal_year,
            'fiscal_quarter': fiscal_quarter,
            'fiscal_month': fiscal_month,
            'fiscal_week': fiscal_week,
            'is_promotional_week': random.random() < 0.15,  # 15% promotional weeks
            'season': season_map[current_date.month],
            'week_of_month': (current_date.day - 1) // 7 + 1
        })

    conn.execute("DELETE FROM dim_date")
    conn.executemany("""
        INSERT INTO dim_date VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, [(d['date_key'], d['date'], d['year'], d['quarter'], d['month'],
           d['month_name'], d['week'], d['day'], d['day_of_week'],
           d['day_name'], d['is_weekend'], d['is_holiday'], d['fiscal_year'],
           d['fiscal_quarter'], d['fiscal_month'], d['fiscal_week'],
           d['is_promotional_week'], d['season'], d['week_of_month']) for d in dates])

    print(f"  Generated {len(dates)} date records")

def generate_product_dimension(conn):
    """Generate product dimension with hierarchy"""
    print("Generating product dimension...")

    categories = [
        {'code': 'BEV', 'name': 'Beverages', 'brands': [
            'Brand-A', 'Brand-B', 'Brand-C'
        ]},
        {'code': 'SNK', 'name': 'Snacks', 'brands': [
            'Brand-D', 'Brand-E', 'Brand-F', 'Brand-G'
        ]},
        {'code': 'DRY', 'name': 'Dairy', 'brands': [
            'Brand-H', 'Brand-I', 'Brand-J'
        ]}
    ]

    pack_sizes = [
        ('200ml', 200, 'ml'), ('500ml', 500, 'ml'), ('1L', 1000, 'ml'), ('2L', 2000, 'ml'),
        ('50gm', 50, 'gm'), ('100gm', 100, 'gm'), ('250gm', 250, 'gm'), ('500gm', 500, 'gm'),
        ('1kg', 1000, 'gm'), ('6pack', 6, 'pieces'), ('12pack', 12, 'pieces')
    ]

    products = []
    product_key = 1

    for category in categories:
        for brand in category['brands']:
            brand_code = brand.replace('Brand-', 'BR')
            num_skus_per_brand = NUM_SKUS // NUM_BRANDS

            for sku_idx in range(num_skus_per_brand):
                pack = random.choice(pack_sizes)
                sku_code = f"{brand_code}{category['code']}{sku_idx+1:03d}"

                products.append({
                    'product_key': product_key,
                    'sku_code': sku_code,
                    'sku_name': f"{brand} {category['name']} {pack[0]}",
                    'brand_name': brand,
                    'brand_code': brand_code,
                    'category_name': category['name'],
                    'category_code': category['code'],
                    'division_name': 'FMCG Division',
                    'manufacturer_name': 'ABC Consumer Products Ltd',
                    'pack_size': pack[0],
                    'pack_size_value': pack[1],
                    'pack_size_unit': pack[2],
                    'mrp': round(random.uniform(10, 500), 2),
                    'product_status': random.choice(['Active'] * 9 + ['Discontinued']),
                    'launch_date': (datetime.now() - timedelta(days=random.randint(30, 1800))).strftime('%Y-%m-%d'),
                    'is_focus_brand': random.random() < 0.3,
                    'hsn_code': f'{random.randint(1000, 9999)}'
                })
                product_key += 1

                if product_key > NUM_SKUS:
                    break
            if product_key > NUM_SKUS:
                break
        if product_key > NUM_SKUS:
            break

    conn.execute("DELETE FROM dim_product")
    conn.executemany("""
        INSERT INTO dim_product VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, [(p['product_key'], p['sku_code'], p['sku_name'], p['brand_name'],
           p['brand_code'], p['category_name'], p['category_code'], p['division_name'],
           p['manufacturer_name'], p['pack_size'], p['pack_size_value'], p['pack_size_unit'],
           p['mrp'], p['product_status'], p['launch_date'], p['is_focus_brand'],
           p['hsn_code']) for p in products])

    print(f"  Generated {len(products)} product records")

def generate_geography_dimension(conn):
    """Generate geography dimension with hierarchy"""
    print("Generating geography dimension...")

    zones = ['North', 'South', 'East', 'West']
    states_by_zone = {
        'North': ['Delhi', 'Punjab', 'Haryana', 'Uttar Pradesh'],
        'South': ['Tamil Nadu', 'Karnataka', 'Kerala', 'Andhra Pradesh'],
        'East': ['West Bengal', 'Odisha', 'Bihar', 'Jharkhand'],
        'West': ['Maharashtra', 'Gujarat', 'Rajasthan']
    }

    outlet_types = ['Kirana', 'Supermarket', 'Hypermarket', 'Medical Store', 'Restaurant']
    classifications = ['A', 'B', 'C']
    tiers = ['Tier-1', 'Tier-2', 'Tier-3']

    geographies = []
    geography_key = 1

    for zone in zones:
        zone_code = zone[:2].upper()
        states = states_by_zone[zone]

        for state in states:
            state_code = ''.join([c for c in state if c.isupper()])[:2]
            num_districts = NUM_DISTRICTS // NUM_STATES

            for dist_idx in range(num_districts):
                district_name = f"{state} District-{dist_idx+1}"
                district_code = f"{state_code}D{dist_idx+1:02d}"
                num_towns = NUM_TOWNS // NUM_DISTRICTS

                for town_idx in range(num_towns):
                    town_name = f"{district_name.split()[0]} Town-{town_idx+1}"
                    town_code = f"{district_code}T{town_idx+1:02d}"
                    num_outlets_per_town = NUM_OUTLETS // NUM_TOWNS

                    for outlet_idx in range(num_outlets_per_town):
                        outlet_type = random.choice(outlet_types)
                        outlet_code = f"{town_code}O{outlet_idx+1:03d}"

                        geographies.append({
                            'geography_key': geography_key,
                            'outlet_code': outlet_code,
                            'outlet_name': f"{outlet_type} {outlet_code}",
                            'town_code': town_code,
                            'town_name': town_name,
                            'district_code': district_code,
                            'district_name': district_name,
                            'state_code': state_code,
                            'state_name': state,
                            'zone_code': zone_code,
                            'zone_name': zone,
                            'region_code': zone_code,
                            'region_name': zone,
                            'outlet_classification': random.choice(classifications),
                            'population_tier': random.choice(tiers),
                            'urban_rural': random.choice(['Urban', 'Rural'])
                        })
                        geography_key += 1

                        if geography_key > NUM_OUTLETS:
                            break
                    if geography_key > NUM_OUTLETS:
                        break
                if geography_key > NUM_OUTLETS:
                    break
            if geography_key > NUM_OUTLETS:
                break
        if geography_key > NUM_OUTLETS:
            break

    conn.execute("DELETE FROM dim_geography")
    conn.executemany("""
        INSERT INTO dim_geography VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, [(g['geography_key'], g['outlet_code'], g['outlet_name'], g['town_code'],
           g['town_name'], g['district_code'], g['district_name'], g['state_code'],
           g['state_name'], g['zone_code'], g['zone_name'], g['region_code'],
           g['region_name'], g['outlet_classification'], g['population_tier'],
           g['urban_rural']) for g in geographies])

    print(f"  Generated {len(geographies)} geography records")

def generate_customer_dimension(conn):
    """Generate customer dimension (distributors and retailers)"""
    print("Generating customer dimension...")

    outlet_types = ['Kirana', 'Supermarket', 'Hypermarket', 'Medical Store', 'Restaurant',
                    'Convenience Store', 'Departmental Store']
    outlet_subtypes = ['Traditional', 'Modern', 'Institutional']
    segments = ['Premium', 'Standard', 'Budget']

    customers = []
    customer_key = 1

    # Generate distributors
    for i in range(1, NUM_DISTRIBUTORS + 1):
        dist_code = f"DIST{i:04d}"
        customers.append({
            'customer_key': customer_key,
            'distributor_code': dist_code,
            'distributor_name': f"Distributor {i}",
            'retailer_code': None,
            'retailer_name': None,
            'outlet_type': 'Distributor',
            'outlet_subtype': 'Direct',
            'customer_segment': random.choice(segments),
            'customer_status': random.choice(['Active'] * 9 + ['Inactive']),
            'credit_limit': round(random.uniform(500000, 5000000), 2),
            'credit_days': random.choice([7, 15, 30, 45]),
            'onboarding_date': (datetime.now() - timedelta(days=random.randint(180, 1800))).strftime('%Y-%m-%d'),
            'last_order_date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
            'gst_number': f"29{random.randint(10000000000, 99999999999)}",
            'pan_number': f"ABCD{random.randint(1000, 9999)}E"
        })
        customer_key += 1

    # Generate retailers
    for i in range(1, NUM_RETAILERS + 1):
        dist_code = f"DIST{random.randint(1, NUM_DISTRIBUTORS):04d}"
        retailer_code = f"RET{i:06d}"

        customers.append({
            'customer_key': customer_key,
            'distributor_code': dist_code,
            'distributor_name': f"Distributor {int(dist_code[4:])}",
            'retailer_code': retailer_code,
            'retailer_name': f"Retailer {i}",
            'outlet_type': random.choice(outlet_types),
            'outlet_subtype': random.choice(outlet_subtypes),
            'customer_segment': random.choice(segments),
            'customer_status': random.choice(['Active'] * 8 + ['Inactive'] * 2),
            'credit_limit': round(random.uniform(10000, 500000), 2),
            'credit_days': random.choice([0, 7, 15, 30]),
            'onboarding_date': (datetime.now() - timedelta(days=random.randint(90, 1800))).strftime('%Y-%m-%d'),
            'last_order_date': (datetime.now() - timedelta(days=random.randint(1, 60))).strftime('%Y-%m-%d'),
            'gst_number': f"29{random.randint(10000000000, 99999999999)}" if random.random() < 0.7 else None,
            'pan_number': f"ABCD{random.randint(1000, 9999)}E" if random.random() < 0.6 else None
        })
        customer_key += 1

    conn.execute("DELETE FROM dim_customer")
    conn.executemany("""
        INSERT INTO dim_customer VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, [(c['customer_key'], c['distributor_code'], c['distributor_name'],
           c['retailer_code'], c['retailer_name'], c['outlet_type'], c['outlet_subtype'],
           c['customer_segment'], c['customer_status'], c['credit_limit'], c['credit_days'],
           c['onboarding_date'], c['last_order_date'], c['gst_number'], c['pan_number'])
          for c in customers])

    print(f"  Generated {len(customers)} customer records")

def generate_channel_dimension(conn):
    """Generate channel dimension"""
    print("Generating channel dimension...")

    channels = [
        (1, 'GT', 'General Trade', 'Indirect', 'Traditional retail through distributors'),
        (2, 'MT', 'Modern Trade', 'Direct', 'Modern retail chains and supermarkets'),
        (3, 'ECOM', 'E-Commerce', 'Direct', 'Online sales platforms'),
        (4, 'IWS', 'Institutional Sales', 'Direct', 'Hotels, Restaurants, Catering'),
        (5, 'PHARM', 'Pharmacy', 'Indirect', 'Medical and pharmacy stores')
    ]

    conn.execute("DELETE FROM dim_channel")
    conn.executemany("""
        INSERT INTO dim_channel VALUES (?, ?, ?, ?, ?)
    """, channels)

    print(f"  Generated {len(channels)} channel records")

def generate_fact_secondary_sales(conn):
    """Generate secondary sales facts"""
    print("Generating secondary sales facts...")

    # Get dimension keys
    date_keys = conn.execute("SELECT date_key FROM dim_date").fetchall()
    date_keys = [d[0] for d in date_keys]

    product_keys = conn.execute("SELECT product_key FROM dim_product WHERE product_status = 'Active'").fetchall()
    product_keys = [p[0] for p in product_keys]

    geography_keys = conn.execute("SELECT geography_key FROM dim_geography").fetchall()
    geography_keys = [g[0] for g in geography_keys]

    customer_keys = conn.execute("SELECT customer_key FROM dim_customer WHERE retailer_code IS NOT NULL AND customer_status = 'Active'").fetchall()
    customer_keys = [c[0] for c in customer_keys]

    channel_keys = [1, 2, 3, 4, 5]

    sales_types = ['Regular', 'Promotional', 'Sample']
    payment_terms = ['Cash', 'Credit']
    payment_statuses = ['Paid', 'Pending', 'Overdue']

    sales = []
    for i in range(1, NUM_SECONDARY_SALES + 1):
        invoice_quantity = random.randint(1, 100)
        base_price = round(random.uniform(50, 500), 2)
        invoice_value = base_price * invoice_quantity
        discount_percentage = random.uniform(0, 25)
        discount_amount = round(invoice_value * discount_percentage / 100, 2)
        tax_amount = round((invoice_value - discount_amount) * 0.18, 2)  # 18% GST
        net_value = round(invoice_value - discount_amount + tax_amount, 2)
        margin_percentage = random.uniform(10, 35)
        margin_amount = round(net_value * margin_percentage / 100, 2)

        date_key = random.choice(date_keys)
        invoice_date = datetime.strptime(str(date_key), '%Y%m%d').strftime('%Y-%m-%d')

        sales.append({
            'sales_key': i,
            'date_key': date_key,
            'product_key': random.choice(product_keys),
            'geography_key': random.choice(geography_keys),
            'customer_key': random.choice(customer_keys),
            'channel_key': random.choice(channel_keys),
            'invoice_number': f"INV{i:08d}",
            'invoice_date': invoice_date,
            'invoice_value': invoice_value,
            'invoice_quantity': invoice_quantity,
            'base_price': base_price,
            'discount_amount': discount_amount,
            'discount_percentage': round(discount_percentage, 2),
            'tax_amount': tax_amount,
            'net_value': net_value,
            'margin_amount': margin_amount,
            'margin_percentage': round(margin_percentage, 2),
            'return_flag': random.random() < 0.02,  # 2% returns
            'return_amount': round(net_value * 0.5, 2) if random.random() < 0.02 else 0,
            'sales_rep_code': f"SR{random.randint(1, 50):03d}",
            'sales_type': random.choice(sales_types),
            'payment_terms': random.choice(payment_terms),
            'payment_status': random.choice(payment_statuses)
        })

    conn.execute("DELETE FROM fact_secondary_sales")
    conn.executemany("""
        INSERT INTO fact_secondary_sales VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, [(s['sales_key'], s['date_key'], s['product_key'], s['geography_key'],
           s['customer_key'], s['channel_key'], s['invoice_number'], s['invoice_date'],
           s['invoice_value'], s['invoice_quantity'], s['base_price'], s['discount_amount'],
           s['discount_percentage'], s['tax_amount'], s['net_value'], s['margin_amount'],
           s['margin_percentage'], s['return_flag'], s['return_amount'], s['sales_rep_code'],
           s['sales_type'], s['payment_terms'], s['payment_status']) for s in sales])

    print(f"  Generated {len(sales)} secondary sales records")

def main():
    """Main function to generate all CPG sample data"""
    db_path = Path(__file__).parent / 'cpg_olap.duckdb'
    schema_path = Path(__file__).parent / 'schema_cpg.sql'

    print(f"Creating CPG database at: {db_path}")

    # Connect to DuckDB
    conn = duckdb.connect(str(db_path))

    # Create schema
    print("Creating schema...")
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
        for statement in schema_sql.split(';'):
            if statement.strip():
                try:
                    conn.execute(statement)
                except Exception as e:
                    print(f"  Warning: {e}")

    # Generate dimensions
    generate_date_dimension(conn)
    generate_product_dimension(conn)
    generate_geography_dimension(conn)
    generate_customer_dimension(conn)
    generate_channel_dimension(conn)

    # Generate facts
    generate_fact_secondary_sales(conn)

    # Show summary
    print("\n" + "="*60)
    print("CPG Database created successfully!")
    print("="*60)
    print("\nTable counts:")
    tables = ['dim_date', 'dim_product', 'dim_geography', 'dim_customer',
              'dim_channel', 'fact_secondary_sales']

    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count:,} records")

    # Show sample queries
    print("\n" + "="*60)
    print("Sample Query Results:")
    print("="*60)

    # Total sales by brand
    print("\nTop 5 Brands by Sales Value:")
    result = conn.execute("""
        SELECT
            p.brand_name,
            COUNT(DISTINCT s.invoice_number) as invoice_count,
            SUM(s.net_value) as total_sales,
            SUM(s.invoice_quantity) as total_quantity
        FROM fact_secondary_sales s
        JOIN dim_product p ON s.product_key = p.product_key
        WHERE s.return_flag = false
        GROUP BY p.brand_name
        ORDER BY total_sales DESC
        LIMIT 5
    """).fetchall()

    for row in result:
        print(f"  {row[0]}: {row[1]:,} invoices, ${row[2]:,.2f}, {row[3]:,} units")

    conn.close()
    print(f"\nDatabase saved to: {db_path}")

if __name__ == '__main__':
    main()
