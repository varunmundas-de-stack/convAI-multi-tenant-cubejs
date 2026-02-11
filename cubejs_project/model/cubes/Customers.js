cube(`Customers`, {
  sql_table: `dim_customer`,

  measures: {
    count: {
      type: `count`,
      description: `Total number of customers`
    },

    active_count: {
      sql: `customer_key`,
      type: `count`,
      filters: [
        { sql: `${CUBE}.customer_status = 'Active'` }
      ],
      description: `Number of active customers`
    },

    average_credit_score: {
      sql: `credit_score`,
      type: `avg`,
      description: `Average credit score`
    }
  },

  dimensions: {
    customer_key: {
      sql: `customer_key`,
      type: `number`,
      primary_key: true
    },

    customer_id: {
      sql: `customer_id`,
      type: `string`
    },

    name: {
      sql: `first_name || ' ' || last_name`,
      type: `string`
    },

    age: {
      sql: `age`,
      type: `number`
    },

    gender: {
      sql: `gender`,
      type: `string`
    },

    occupation: {
      sql: `occupation`,
      type: `string`
    },

    income_bracket: {
      sql: `income_bracket`,
      type: `string`
    },

    credit_score: {
      sql: `credit_score`,
      type: `number`
    },

    customer_segment: {
      sql: `customer_segment`,
      type: `string`
    },

    city: {
      sql: `city`,
      type: `string`
    },

    state: {
      sql: `state`,
      type: `string`
    },

    customer_status: {
      sql: `customer_status`,
      type: `string`
    }
  }
});
