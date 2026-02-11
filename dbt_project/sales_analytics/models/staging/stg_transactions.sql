-- Staging model for transactions
-- Cleans and standardizes transaction data

with source as (
    select * from {{ source('bfsi', 'fact_transactions') }}
),

renamed as (
    select
        transaction_key,
        date_key,
        customer_key,
        account_key,
        transaction_type_key,
        transaction_amount,
        transaction_fee,
        balance_after_transaction,
        transaction_status
    from source
)

select * from renamed
