// DimProduct — product hierarchy dimension

const clientId = COMPILE_CONTEXT.securityContext && COMPILE_CONTEXT.securityContext.clientId
  ? COMPILE_CONTEXT.securityContext.clientId
  : 'nestle';

const schema = `client_${clientId}`;

cube('DimProduct', {
  sql: `SELECT * FROM ${schema}.dim_product`,

  measures: {
    count: {
      type: `count`,
      drillMembers: [product_key, sku_name],
    },
  },

  dimensions: {
    product_key: {
      sql: `product_key`,
      type: `number`,
      primaryKey: true,
    },

    sku_name: {
      sql: `sku_name`,
      type: `string`,
      title: `SKU Name`,
    },

    brand_name: {
      sql: `brand_name`,
      type: `string`,
      title: `Brand Name`,
    },

    category_name: {
      sql: `category_name`,
      type: `string`,
      title: `Category Name`,
    },

    sub_category: {
      sql: `sub_category`,
      type: `string`,
      title: `Sub Category`,
    },

    pack_size: {
      sql: `pack_size`,
      type: `string`,
      title: `Pack Size`,
    },
  },
});
