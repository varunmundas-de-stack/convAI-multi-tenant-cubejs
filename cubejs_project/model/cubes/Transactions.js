cube(`Transactions`, {
  sql_table: `fact_transactions`,

  joins: {
    Customers: {
      sql: `${CUBE}.customer_key = ${Customers}.customer_key`,
      relationship: `many_to_one`
    },

    Accounts: {
      sql: `${CUBE}.account_key = ${Accounts}.account_key`,
      relationship: `many_to_one`
    },

    Dates: {
      sql: `${CUBE}.date_key = ${Dates}.date_key`,
      relationship: `many_to_one`
    },

    TransactionTypes: {
      sql: `${CUBE}.transaction_type_key = ${TransactionTypes}.transaction_type_key`,
      relationship: `many_to_one`
    }
  },

  measures: {
    count: {
      type: `count`,
      description: `Total number of transactions`
    },

    total_amount: {
      sql: `transaction_amount`,
      type: `sum`,
      description: `Total transaction amount`,
      format: `currency`
    },

    average_amount: {
      sql: `transaction_amount`,
      type: `avg`,
      description: `Average transaction amount`,
      format: `currency`
    },

    total_fees: {
      sql: `transaction_fee`,
      type: `sum`,
      description: `Total transaction fees`,
      format: `currency`
    }
  },

  dimensions: {
    transaction_key: {
      sql: `transaction_key`,
      type: `number`,
      primary_key: true
    },

    transaction_status: {
      sql: `transaction_status`,
      type: `string`
    },

    channel: {
      sql: `channel`,
      type: `string`
    },

    balance_after: {
      sql: `balance_after_transaction`,
      type: `number`,
      format: `currency`
    }
  },

  pre_aggregations: {
    daily_summary: {
      measures: [count, total_amount, average_amount, total_fees],
      time_dimension: Dates.date,
      granularity: `day`,
      partition_granularity: `month`,
      refresh_key: {
        every: `1 hour`
      }
    },

    monthly_summary: {
      measures: [count, total_amount, average_amount],
      time_dimension: Dates.date,
      granularity: `month`,
      refresh_key: {
        every: `1 day`
      }
    }
  }
});
