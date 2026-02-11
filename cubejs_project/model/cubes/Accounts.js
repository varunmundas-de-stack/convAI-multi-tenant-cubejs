cube(`Accounts`, {
  sql_table: `dim_account`,

  measures: {
    count: {
      type: `count`,
      description: `Total number of accounts`
    },

    active_count: {
      sql: `account_key`,
      type: `count`,
      filters: [
        { sql: `${CUBE}.account_status = 'Active'` }
      ],
      description: `Number of active accounts`
    }
  },

  dimensions: {
    account_key: {
      sql: `account_key`,
      type: `number`,
      primary_key: true
    },

    account_id: {
      sql: `account_id`,
      type: `string`
    },

    account_type: {
      sql: `account_type`,
      type: `string`
    },

    account_subtype: {
      sql: `account_subtype`,
      type: `string`
    },

    branch_name: {
      sql: `branch_name`,
      type: `string`
    },

    region: {
      sql: `region`,
      type: `string`
    },

    account_status: {
      sql: `account_status`,
      type: `string`
    },

    interest_rate: {
      sql: `interest_rate`,
      type: `number`
    }
  }
});
