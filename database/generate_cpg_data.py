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
    """Generate product dimension with hierarchy including subcategories"""
    print("Generating product dimension...")

    categories = [
        {'code': 'BEV', 'name': 'Beverages', 'subcategories': [
            {'code': 'SOFT', 'name': 'Soft Drinks', 'brands': ['Brand-A', 'Brand-B']},
            {'code': 'JUICE', 'name': 'Juices', 'brands': ['Brand-C']}
        ]},
        {'code': 'SNK', 'name': 'Snacks', 'subcategories': [
            {'code': 'CHIPS', 'name': 'Chips', 'brands': ['Brand-D', 'Brand-E']},
            {'code': 'BISC', 'name': 'Biscuits', 'brands': ['Brand-F', 'Brand-G']}
        ]},
        {'code': 'DRY', 'name': 'Dairy', 'subcategories': [
            {'code': 'MILK', 'name': 'Milk Products', 'brands': ['Brand-H', 'Brand-I']},
            {'code': 'YOG', 'name': 'Yogurt', 'brands': ['Brand-J']}
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
        for subcategory in category['subcategories']:
            for brand in subcategory['brands']:
                brand_code = brand.replace('Brand-', 'BR')
                num_skus_per_brand = NUM_SKUS // NUM_BRANDS

                for sku_idx in range(num_skus_per_brand):
                    pack = random.choice(pack_sizes)
                    sku_code = f"{brand_code}{subcategory['code']}{sku_idx+1:03d}"

                    products.append({
                        'product_key': product_key,
                        'sku_code': sku_code,
                        'sku_name': f"{brand} {subcategory['name']} {pack[0]}",
                        'brand_name': brand,
                        'brand_code': brand_code,
                        'category_name': category['name'],
                        'category_code': category['code'],
                        'subcategory_code': subcategory['code'],
                        'subcategory_name': subcategory['name'],
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
        if product_key > NUM_SKUS:
            break

    conn.execute("DELETE FROM dim_product")
    conn.executemany("""
        INSERT INTO dim_product VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, [(p['product_key'], p['sku_code'], p['sku_name'], p['brand_name'],
           p['brand_code'], p['category_name'], p['category_code'], p['subcategory_code'],
           p['subcategory_name'], p['division_name'], p['manufacturer_name'], p['pack_size'],
           p['pack_size_value'], p['pack_size_unit'], p['mrp'], p['product_status'],
           p['launch_date'], p['is_focus_brand'], p['hsn_code']) for p in products])

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

def generate_sales_hierarchy_dimension(conn):
    """Generate sales hierarchy dimension (SO → ASM → ZSM → NSM)"""
    print("Generating sales hierarchy dimension...")

    hierarchies = []
    hierarchy_key = 1

    # 2 NSMs (National Sales Managers)
    nsms = [
        {'code': 'NSM01', 'name': 'Rajesh Kumar', 'emp_id': 'E1001'},
        {'code': 'NSM02', 'name': 'Priya Sharma', 'emp_id': 'E1002'}
    ]

    zones = ['North', 'South', 'East', 'West']

    for nsm in nsms:
        # 2 ZSMs per NSM (4 zones)
        for zsm_idx in range(2):
            zone = zones[nsms.index(nsm) * 2 + zsm_idx]
            zsm_code = f"ZSM{nsms.index(nsm) * 2 + zsm_idx + 1:02d}"
            zsm = {
                'code': zsm_code,
                'name': f"ZSM {zone}",
                'emp_id': f"E20{nsms.index(nsm) * 2 + zsm_idx + 1:02d}"
            }

            # 2 ASMs per ZSM (8 regions)
            for asm_idx in range(2):
                asm_code = f"{zsm_code}_ASM{asm_idx + 1}"
                region_code = f"RG{(nsms.index(nsm) * 4 + zsm_idx * 2 + asm_idx + 1):02d}"
                asm = {
                    'code': asm_code,
                    'name': f"ASM {zone} Region-{asm_idx + 1}",
                    'emp_id': f"E30{(nsms.index(nsm) * 4 + zsm_idx * 2 + asm_idx + 1):02d}"
                }

                # 5 SOs per ASM (40 territories)
                for so_idx in range(5):
                    so_code = f"{asm_code}_SO{so_idx + 1:02d}"
                    territory_code = f"TER{hierarchy_key:03d}"

                    hierarchies.append({
                        'sales_hierarchy_key': hierarchy_key,
                        'so_code': so_code,
                        'so_name': f"Sales Officer {hierarchy_key}",
                        'so_employee_id': f"E40{hierarchy_key:03d}",
                        'asm_code': asm['code'],
                        'asm_name': asm['name'],
                        'asm_employee_id': asm['emp_id'],
                        'zsm_code': zsm['code'],
                        'zsm_name': zsm['name'],
                        'zsm_employee_id': zsm['emp_id'],
                        'nsm_code': nsm['code'],
                        'nsm_name': nsm['name'],
                        'nsm_employee_id': nsm['emp_id'],
                        'territory_code': territory_code,
                        'territory_name': f"Territory {hierarchy_key}",
                        'region_code': region_code,
                        'region_name': f"{zone} Region-{asm_idx + 1}",
                        'zone_code': zone[:2].upper(),
                        'zone_name': zone,
                        'is_active': True,
                        'effective_date': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                        'expiry_date': None
                    })
                    hierarchy_key += 1

    conn.execute("DELETE FROM dim_sales_hierarchy")
    conn.executemany("""
        INSERT INTO dim_sales_hierarchy VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, [(h['sales_hierarchy_key'], h['so_code'], h['so_name'], h['so_employee_id'],
           h['asm_code'], h['asm_name'], h['asm_employee_id'], h['zsm_code'],
           h['zsm_name'], h['zsm_employee_id'], h['nsm_code'], h['nsm_name'],
           h['nsm_employee_id'], h['territory_code'], h['territory_name'],
           h['region_code'], h['region_name'], h['zone_code'], h['zone_name'],
           h['is_active'], h['effective_date'], h['expiry_date']) for h in hierarchies])

    print(f"  Generated {len(hierarchies)} sales hierarchy records")
    return hierarchies

def generate_companywh_dimension():
    """Generate company warehouse dimension"""
    warehouses = [
        {'code': 'WH01', 'name': 'Mumbai Warehouse'},
        {'code': 'WH02', 'name': 'Delhi Warehouse'},
        {'code': 'WH03', 'name': 'Bangalore Warehouse'},
        {'code': 'WH04', 'name': 'Chennai Warehouse'},
        {'code': 'WH05', 'name': 'Kolkata Warehouse'},
        {'code': 'WH06', 'name': 'Hyderabad Warehouse'},
        {'code': 'WH07', 'name': 'Pune Warehouse'},
        {'code': 'WH08', 'name': 'Ahmedabad Warehouse'}
    ]
    return warehouses

def generate_fact_primary_sales(conn, warehouses):
    """Generate primary sales facts (manufacturer to distributor)"""
    print("Generating primary sales facts...")

    # Get dimension keys
    date_keys = conn.execute("SELECT date_key FROM dim_date").fetchall()
    date_keys = [d[0] for d in date_keys]

    product_keys = conn.execute("SELECT product_key FROM dim_product WHERE product_status = 'Active'").fetchall()
    product_keys = [p[0] for p in product_keys]

    # Get distributors only
    customer_keys = conn.execute("SELECT customer_key FROM dim_customer WHERE outlet_type = 'Distributor' AND customer_status = 'Active'").fetchall()
    customer_keys = [c[0] for c in customer_keys]

    channel_keys = [1, 2, 3, 4, 5]

    # Generate 500 primary sales records
    num_primary_sales = 500
    primary_sales = []

    for i in range(1, num_primary_sales + 1):
        order_quantity = random.randint(100, 5000)
        order_value = round(order_quantity * random.uniform(40, 400), 2)
        dispatch_quantity = int(order_quantity * random.uniform(0.8, 1.0))
        dispatch_value = round(dispatch_quantity * (order_value / order_quantity), 2)
        pending_quantity = order_quantity - dispatch_quantity
        freight_cost = round(dispatch_value * random.uniform(0.02, 0.05), 2)

        date_key = random.choice(date_keys)
        order_date = datetime.strptime(str(date_key), '%Y%m%d').strftime('%Y-%m-%d')

        warehouse = random.choice(warehouses)

        primary_sales.append({
            'primary_sales_key': i,
            'date_key': date_key,
            'product_key': random.choice(product_keys),
            'customer_key': random.choice(customer_keys),
            'channel_key': random.choice(channel_keys),
            'order_number': f"PO{i:08d}",
            'order_date': order_date,
            'order_quantity': order_quantity,
            'order_value': order_value,
            'dispatch_quantity': dispatch_quantity,
            'dispatch_value': dispatch_value,
            'pending_quantity': pending_quantity,
            'freight_cost': freight_cost,
            'companywh_code': warehouse['code'],
            'companywh_name': warehouse['name']
        })

    conn.execute("DELETE FROM fact_primary_sales")
    conn.executemany("""
        INSERT INTO fact_primary_sales VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, [(s['primary_sales_key'], s['date_key'], s['product_key'], s['customer_key'],
           s['channel_key'], s['order_number'], s['order_date'], s['order_quantity'],
           s['order_value'], s['dispatch_quantity'], s['dispatch_value'],
           s['pending_quantity'], s['freight_cost'], s['companywh_code'],
           s['companywh_name']) for s in primary_sales])

    print(f"  Generated {len(primary_sales)} primary sales records")

def generate_fact_secondary_sales(conn, sales_hierarchies):
    """Generate secondary sales facts with weight/volume and sales hierarchy"""
    print("Generating secondary sales facts...")

    # Get dimension keys
    date_keys = conn.execute("SELECT date_key FROM dim_date").fetchall()
    date_keys = [d[0] for d in date_keys]

    # Get products with pack size info for weight/volume calculation
    products = conn.execute("""
        SELECT product_key, pack_size_unit, pack_size_value
        FROM dim_product
        WHERE product_status = 'Active'
    """).fetchall()
    products = [{'key': p[0], 'unit': p[1], 'value': p[2]} for p in products]

    geography_keys = conn.execute("SELECT geography_key FROM dim_geography").fetchall()
    geography_keys = [g[0] for g in geography_keys]

    customer_keys = conn.execute("SELECT customer_key FROM dim_customer WHERE retailer_code IS NOT NULL AND customer_status = 'Active'").fetchall()
    customer_keys = [c[0] for c in customer_keys]

    channel_keys = [1, 2, 3, 4, 5]
    hierarchy_keys = [h['sales_hierarchy_key'] for h in sales_hierarchies]

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

        # Select product and calculate weight/volume
        product = random.choice(products)
        unit_weight = 0.0
        unit_volume = 0.0

        if product['unit'] == 'gm':
            unit_weight = product['value'] / 1000  # Convert to kg
        elif product['unit'] == 'ml':
            unit_volume = product['value'] / 1000  # Convert to liters

        total_weight = round(unit_weight * invoice_quantity, 3)
        total_volume = round(unit_volume * invoice_quantity, 3)

        sales.append({
            'sales_key': i,
            'date_key': date_key,
            'product_key': product['key'],
            'geography_key': random.choice(geography_keys),
            'customer_key': random.choice(customer_keys),
            'channel_key': random.choice(channel_keys),
            'sales_hierarchy_key': random.choice(hierarchy_keys),
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
            'payment_status': random.choice(payment_statuses),
            'unit_weight': unit_weight,
            'unit_volume': unit_volume,
            'total_weight': total_weight,
            'total_volume': total_volume
        })

    conn.execute("DELETE FROM fact_secondary_sales")
    conn.executemany("""
        INSERT INTO fact_secondary_sales VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, [(s['sales_key'], s['date_key'], s['product_key'], s['geography_key'],
           s['customer_key'], s['channel_key'], s['sales_hierarchy_key'], s['invoice_number'],
           s['invoice_date'], s['invoice_value'], s['invoice_quantity'], s['base_price'],
           s['discount_amount'], s['discount_percentage'], s['tax_amount'], s['net_value'],
           s['margin_amount'], s['margin_percentage'], s['return_flag'], s['return_amount'],
           s['sales_rep_code'], s['sales_type'], s['payment_terms'], s['payment_status'],
           s['unit_weight'], s['unit_volume'], s['total_weight'], s['total_volume']) for s in sales])

    print(f"  Generated {len(sales)} secondary sales records")

def generate_fact_inventory(conn):
    """Generate inventory facts (opening/closing stock per product per outlet)"""
    print("Generating inventory facts...")

    date_keys = conn.execute("SELECT date_key FROM dim_date ORDER BY date_key").fetchall()
    # Use weekly snapshots — pick one date per week
    weekly_dates = [date_keys[i][0] for i in range(0, len(date_keys), 7)]

    product_keys = conn.execute("SELECT product_key FROM dim_product WHERE product_status = 'Active'").fetchall()
    product_keys = [p[0] for p in product_keys]

    geography_keys = conn.execute("SELECT geography_key FROM dim_geography").fetchall()
    geography_keys = [g[0] for g in geography_keys]

    customer_keys = conn.execute("SELECT customer_key FROM dim_customer WHERE retailer_code IS NOT NULL").fetchall()
    customer_keys = [c[0] for c in customer_keys]

    stock_statuses = ['Normal', 'Below Reorder', 'Overstock', 'Out of Stock']
    stock_status_weights = [0.6, 0.2, 0.1, 0.1]

    records = []
    inventory_key = 1
    # Generate ~200 records: sample products × weekly dates
    for date_key in weekly_dates[:4]:  # 4 weekly snapshots
        for product_key in random.sample(product_keys, min(50, len(product_keys))):
            reorder_level = random.randint(20, 100)
            max_stock = reorder_level * random.randint(3, 8)
            opening_stock = random.randint(0, max_stock)
            receipts = random.randint(0, max_stock // 2)
            issues = random.randint(0, min(opening_stock + receipts, max_stock // 2))
            closing_stock = opening_stock + receipts - issues
            stock_value = round(closing_stock * random.uniform(40, 400), 2)
            days_of_supply = round(closing_stock / max(issues, 1) * 7, 1) if issues > 0 else 999.9

            if closing_stock == 0:
                status = 'Out of Stock'
            elif closing_stock < reorder_level:
                status = 'Below Reorder'
            elif closing_stock > max_stock:
                status = 'Overstock'
            else:
                status = 'Normal'

            records.append((
                inventory_key, date_key, product_key,
                random.choice(geography_keys), random.choice(customer_keys),
                opening_stock, closing_stock, receipts, issues, stock_value,
                days_of_supply, reorder_level, max_stock, status
            ))
            inventory_key += 1

    conn.execute("DELETE FROM fact_inventory")
    conn.executemany("""
        INSERT INTO fact_inventory VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)

    print(f"  Generated {len(records)} inventory records")


def generate_fact_distribution(conn):
    """Generate distribution metrics per product per geography per week"""
    print("Generating distribution facts...")

    date_keys = conn.execute("SELECT date_key FROM dim_date ORDER BY date_key").fetchall()
    weekly_dates = [date_keys[i][0] for i in range(0, len(date_keys), 7)]

    product_keys = conn.execute("SELECT product_key FROM dim_product WHERE product_status = 'Active'").fetchall()
    product_keys = [p[0] for p in product_keys]

    geography_keys = conn.execute("SELECT geography_key FROM dim_geography").fetchall()
    geography_keys = [g[0] for g in geography_keys]

    channel_keys = [1, 2, 3, 4, 5]

    records = []
    dist_key = 1
    for date_key in weekly_dates[:4]:  # 4 weekly snapshots
        for product_key in random.sample(product_keys, min(50, len(product_keys))):
            total_outlets = random.randint(50, 500)
            outlets_with_stock = random.randint(int(total_outlets * 0.3), total_outlets)
            outlets_with_sales = random.randint(int(outlets_with_stock * 0.5), outlets_with_stock)
            out_of_stock = total_outlets - outlets_with_stock
            numeric_dist = round((outlets_with_sales / total_outlets) * 100, 2)
            weighted_dist = round(numeric_dist * random.uniform(0.8, 1.2), 2)
            weighted_dist = min(weighted_dist, 100.0)
            share_of_shelf = round(random.uniform(5, 40), 2)
            avg_facing = round(random.uniform(1.5, 6.0), 2)

            records.append((
                dist_key, date_key, product_key,
                random.choice(geography_keys), random.choice(channel_keys),
                total_outlets, outlets_with_stock, outlets_with_sales,
                numeric_dist, weighted_dist, share_of_shelf,
                out_of_stock, avg_facing
            ))
            dist_key += 1

    conn.execute("DELETE FROM fact_distribution")
    conn.executemany("""
        INSERT INTO fact_distribution VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)

    print(f"  Generated {len(records)} distribution records")


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
    sales_hierarchies = generate_sales_hierarchy_dimension(conn)
    warehouses = generate_companywh_dimension()

    # Generate facts
    generate_fact_primary_sales(conn, warehouses)
    generate_fact_secondary_sales(conn, sales_hierarchies)
    generate_fact_inventory(conn)
    generate_fact_distribution(conn)

    # Show summary
    print("\n" + "="*60)
    print("CPG Database created successfully!")
    print("="*60)
    print("\nTable counts:")
    tables = ['dim_date', 'dim_product', 'dim_geography', 'dim_customer',
              'dim_channel', 'dim_sales_hierarchy', 'fact_primary_sales',
              'fact_secondary_sales', 'fact_inventory', 'fact_distribution']

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
