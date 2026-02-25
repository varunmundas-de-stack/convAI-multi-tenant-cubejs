// DimChannel — sales channel dimension

const clientId = COMPILE_CONTEXT.securityContext && COMPILE_CONTEXT.securityContext.clientId
  ? COMPILE_CONTEXT.securityContext.clientId
  : 'nestle';

const schema = `client_${clientId}`;

cube('DimChannel', {
  sql: `SELECT * FROM ${schema}.dim_channel`,

  measures: {
    count: {
      type: `count`,
      drillMembers: [channel_key, channel_name],
    },
  },

  dimensions: {
    channel_key: {
      sql: `channel_key`,
      type: `number`,
      primaryKey: true,
    },

    channel_name: {
      sql: `channel_name`,
      type: `string`,
      title: `Channel`,
    },

    channel_type: {
      sql: `channel_type`,
      type: `string`,
      title: `Channel Type`,
    },
  },
});
