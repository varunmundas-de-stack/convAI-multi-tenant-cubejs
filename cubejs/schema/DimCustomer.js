// DimCustomer — customer hierarchy dimension

const clientId = COMPILE_CONTEXT.securityContext && COMPILE_CONTEXT.securityContext.clientId
  ? COMPILE_CONTEXT.securityContext.clientId
  : 'nestle';

const schema = `client_${clientId}`;

cube('DimCustomer', {
  sql: `SELECT * FROM ${schema}.dim_customer`,

  measures: {
    count: {
      type: `count`,
      drillMembers: [customer_key, distributor_name],
    },
  },

  dimensions: {
    customer_key: {
      sql: `customer_key`,
      type: `number`,
      primaryKey: true,
    },

    distributor_name: {
      sql: `distributor_name`,
      type: `string`,
      title: `Distributor`,
    },

    retailer_name: {
      sql: `retailer_name`,
      type: `string`,
      title: `Retailer`,
    },

    outlet_type: {
      sql: `outlet_type`,
      type: `string`,
      title: `Outlet Type`,
    },

    customer_code: {
      sql: `customer_code`,
      type: `string`,
      title: `Customer Code`,
    },
  },
});
