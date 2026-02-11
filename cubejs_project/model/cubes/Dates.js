cube(`Dates`, {
  sql_table: `dim_date`,

  dimensions: {
    date_key: {
      sql: `date_key`,
      type: `number`,
      primary_key: true
    },

    date: {
      sql: `date`,
      type: `time`
    },

    year: {
      sql: `year`,
      type: `number`
    },

    quarter: {
      sql: `quarter`,
      type: `number`
    },

    month: {
      sql: `month`,
      type: `number`
    },

    month_name: {
      sql: `month_name`,
      type: `string`
    },

    week: {
      sql: `week`,
      type: `number`
    },

    day_name: {
      sql: `day_name`,
      type: `string`
    },

    is_weekend: {
      sql: `is_weekend`,
      type: `boolean`
    },

    is_holiday: {
      sql: `is_holiday`,
      type: `boolean`
    }
  }
});
