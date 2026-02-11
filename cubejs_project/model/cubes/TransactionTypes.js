cube(`TransactionTypes`, {
  sql_table: `dim_transaction_type`,

  dimensions: {
    transaction_type_key: {
      sql: `transaction_type_key`,
      type: `number`,
      primary_key: true
    },

    transaction_type: {
      sql: `transaction_type`,
      type: `string`
    },

    transaction_category: {
      sql: `transaction_category`,
      type: `string`
    },

    is_credit: {
      sql: `is_credit`,
      type: `boolean`
    },

    is_debit: {
      sql: `is_debit`,
      type: `boolean`
    }
  }
});
