// FactSecondarySales — main fact table
// COMPILE_CONTEXT.securityContext.clientId drives multi-tenant schema switching

const clientId = COMPILE_CONTEXT.securityContext && COMPILE_CONTEXT.securityContext.clientId
  ? COMPILE_CONTEXT.securityContext.clientId
  : 'nestle';

const schema = `client_${clientId}`;

cube('FactSecondarySales', {
  sql: `SELECT * FROM ${schema}.fact_secondary_sales`,

  // ────────────────────────────────────────────────────────────────────────
  // Joins to dimension tables (all LEFT OUTER on *_key)
  // ────────────────────────────────────────────────────────────────────────
  joins: {
    DimProduct: {
      sql: `${CUBE}.product_key = ${DimProduct}.product_key`,
      relationship: 'manyToOne',
    },
    DimGeography: {
      sql: `${CUBE}.geography_key = ${DimGeography}.geography_key`,
      relationship: 'manyToOne',
    },
    DimCustomer: {
      sql: `${CUBE}.customer_key = ${DimCustomer}.customer_key`,
      relationship: 'manyToOne',
    },
    DimChannel: {
      sql: `${CUBE}.channel_key = ${DimChannel}.channel_key`,
      relationship: 'manyToOne',
    },
    DimDate: {
      sql: `${CUBE}.date_key = ${DimDate}.date_key`,
      relationship: 'manyToOne',
    },
    DimSalesHierarchy: {
      sql: `${CUBE}.sales_hierarchy_key = ${DimSalesHierarchy}.hierarchy_key`,
      relationship: 'manyToOne',
    },
  },

  // ────────────────────────────────────────────────────────────────────────
  // Measures (6 — matching YAML metric definitions)
  // ────────────────────────────────────────────────────────────────────────
  measures: {
    secondary_sales_value: {
      sql: `net_value`,
      type: `sum`,
      title: `Secondary Sales Value`,
      description: `Net invoiced value to retailers`,
      format: `currency`,
    },

    secondary_sales_volume: {
      sql: `invoice_quantity`,
      type: `sum`,
      title: `Secondary Sales Volume`,
      description: `Total units sold to retailers`,
      format: `number`,
    },

    gross_sales_value: {
      sql: `invoice_value`,
      type: `sum`,
      title: `Gross Sales Value`,
      description: `Gross sales value before discounts`,
      format: `currency`,
    },

    discount_amount: {
      sql: `discount_amount`,
      type: `sum`,
      title: `Discount Amount`,
      description: `Total discount given`,
      format: `currency`,
    },

    margin_amount: {
      sql: `margin_amount`,
      type: `sum`,
      title: `Margin Amount`,
      description: `Total margin earned`,
      format: `currency`,
    },

    invoice_count: {
      sql: `invoice_number`,
      type: `countDistinct`,
      title: `Invoice Count`,
      description: `Number of distinct invoices`,
      format: `number`,
    },
  },

  // ────────────────────────────────────────────────────────────────────────
  // Dimensions on the fact table itself (dates, keys)
  // ────────────────────────────────────────────────────────────────────────
  dimensions: {
    invoice_number: {
      sql: `invoice_number`,
      type: `string`,
      primaryKey: true,
    },

    invoice_date: {
      sql: `invoice_date`,
      type: `time`,
      title: `Invoice Date`,
    },

    product_key: {
      sql: `product_key`,
      type: `number`,
      shown: false,
    },

    geography_key: {
      sql: `geography_key`,
      type: `number`,
      shown: false,
    },

    customer_key: {
      sql: `customer_key`,
      type: `number`,
      shown: false,
    },

    channel_key: {
      sql: `channel_key`,
      type: `number`,
      shown: false,
    },

    date_key: {
      sql: `date_key`,
      type: `number`,
      shown: false,
    },

    sales_hierarchy_key: {
      sql: `sales_hierarchy_key`,
      type: `number`,
      shown: false,
    },
  },

  // Pre-aggregations for common query patterns (optional — can be disabled)
  preAggregations: {
    monthly_by_brand: {
      measures: [
        'FactSecondarySales.secondary_sales_value',
        'FactSecondarySales.secondary_sales_volume',
        'FactSecondarySales.invoice_count',
      ],
      dimensions: [
        'DimProduct.brand_name',
        'DimDate.month',
      ],
      timeDimension: 'FactSecondarySales.invoice_date',
      granularity: `month`,
      refreshKey: {
        every: `1 day`,
      },
    },
  },
});
