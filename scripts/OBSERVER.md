# Progressive Mutation Observer

Use the `observe.py` script to watch how data mutations propagate through your dbt pipeline in real-time.

## Quick Start

### Interactive Mode (Recommended)
```bash
cd ecommerce
python ../scripts/observe.py
```

This launches an interactive loop where you:
1. **See current state** (OLTP, staging, marts)
2. **Choose a mutation** (insert, update, delete, soft-delete, bugs, etc.)
3. **Watch dbt build** run automatically
4. **Compare before/after** state
5. **Repeat** for next observation

### Single Mutation Mode
```bash
cd ecommerce
python ../scripts/observe.py --action insert-customer
python ../scripts/observe.py --action soft-delete-order
python ../scripts/observe.py --action bug-negative-amount --skip-dbt
```

## What You'll Observe

### Normal Operations
- **insert-customer**: New customer appears in dim_customers
- **insert-order**: New order flows through fct_orders → mart_customer_sales
- **update-customer**: Country change triggers snapshot SCD Type 2 record
- **update-order**: Status change updates is_paid, is_refunded, recognized_revenue

### Soft Delete Pattern
- **soft-delete-order**: deleted_at is set, fct_orders retains row, aggregations exclude it
- **restore-order**: deleted_at cleared, order comes back to mart aggregations

### Late-Arriving Data
- **late-arriving-order**: Order with past order_date gets incremental merge
- **backdate-update**: Updated_at moved back (tests incremental logic)

### Data Quality Issues
- **bug-invalid-country**: Triggers relationship test failure
- **bug-negative-amount**: Triggers positive_values test failure
- **bug-zero-amount**: Triggers positive_values test failure
- **bug-future-order**: Triggers future date test failure

## Key Observations

Each iteration shows:

```
📊 BEFORE MUTATION
  orders_summary:
    • total_orders: 10
    • active_orders: 8
    • fct_orders_count: 8

🔄 Applying mutation: insert-order

🏗️  Running dbt build...
  ✅ dbt build completed successfully

📊 AFTER MUTATION + dbt build
  orders_summary:
    • total_orders: 11
    • active_orders: 9
    • fct_orders_count: 9
```

## Mutation Categories

1. **Normal Operations**: Standard insert/update/delete cycles
2. **Soft Delete & Restore**: SCD Type 1 preservation pattern
3. **Advanced Patterns**: Late arrivals, stale records
4. **Data Quality Issues**: Invalid states that should fail tests

## Example Workflow

```bash
1. Start with clean database:
   docker compose down -v && docker compose up -d

2. Run dbt build once:
   cd ecommerce && dbt build

3. Start observer:
   python ../scripts/observe.py

4. Follow prompts:
   - Option 1: insert-customer
   - See how it flows to dim_customers
   - Option 8: bug-negative-amount
   - See test failure
   - Continue exploring...
```

## Database Schema

Observer tracks:
- **shop schema**: OLTP source (customers, orders)
- **shop schema**: Staging (stg_customers, stg_orders)
- **shop schema**: Intermediate (int_customers_enriched, int_orders_by_customer)
- **analytics schema**: Marts (dim_customers, fct_orders, mart_customer_sales)
- **analytics schema**: Snapshots (customers_snapshot)

Each view shows COUNT(*), aggregations, and timestamps to track pipeline flow.
