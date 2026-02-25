// DimDate — time dimension with grain-level columns

const clientId = COMPILE_CONTEXT.securityContext && COMPILE_CONTEXT.securityContext.clientId
  ? COMPILE_CONTEXT.securityContext.clientId
  : 'nestle';

const schema = `client_${clientId}`;

cube('DimDate', {
  sql: `SELECT * FROM ${schema}.dim_date`,

  measures: {
    count: {
      type: `count`,
    },
  },

  dimensions: {
    date_key: {
      sql: `date_key`,
      type: `number`,
      primaryKey: true,
    },

    full_date: {
      sql: `full_date`,
      type: `time`,
      title: `Date`,
    },

    year: {
      sql: `year`,
      type: `number`,
      title: `Year`,
    },

    quarter: {
      sql: `quarter`,
      type: `string`,
      title: `Quarter`,
    },

    month: {
      sql: `month`,
      type: `number`,
      title: `Month`,
    },

    month_name: {
      sql: `month_name`,
      type: `string`,
      title: `Month Name`,
    },

    week: {
      sql: `week`,
      type: `number`,
      title: `Week`,
    },

    week_label: {
      sql: `week_label`,
      type: `string`,
      title: `Week Label`,
    },

    day_of_week: {
      sql: `day_of_week`,
      type: `string`,
      title: `Day of Week`,
    },
  },
});
