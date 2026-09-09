#!/usr/bin/env python3
"""
observe.py - Interactive progressive data mutation and observation tool with real diffs.

Allows you to:
1. View affected rows before mutation
2. Apply a mutation (insert, update, delete, bugs)
3. Run dbt build automatically (full dependency update)
4. Compare affected rows after mutation (showing actual diff)
5. Repeat for next observation

Usage:
    python observe.py              # Interactive mode
    python observe.py --action insert-customer  # Run specific mutation
    python observe.py --action insert-order      # Always runs dbt build
"""

import argparse
import subprocess
import sys
import os
from datetime import datetime, timedelta
import random
import time
from typing import Dict, Optional, Tuple

import psycopg
from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')

DSN = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Import mutation functions from mutate.py
import importlib.util
spec = importlib.util.spec_from_file_location("mutate", os.path.join(os.path.dirname(__file__), "mutate.py"))
mutate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mutate_module)

_has_customers = mutate_module._has_customers
_has_orders = mutate_module._has_orders
_has_active_orders = mutate_module._has_active_orders
_has_deleted_orders = mutate_module._has_deleted_orders
_has_customer_with_orders = mutate_module._has_customer_with_orders

# ============================================================================
# Mutation → Affected Tables Mapping
# ============================================================================

def _select_one_value(conn, sql: str, params: Tuple = ()):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    return row[0] if row else None


def _prepare_mutation_context(conn, mutation_name: str) -> Dict:
    """Pick the exact target row that will be mutated, so BEFORE/AFTER stay aligned."""
    if mutation_name in {"update-customer"}:
        customer_id = _select_one_value(
            conn,
            "select customer_id from shop.customers order by random() limit 1",
        )
        return {"customer_id": customer_id} if customer_id is not None else {}

    if mutation_name in {"insert-order", "late-arriving-order"}:
        customer_id = _select_one_value(
            conn,
            "select customer_id from shop.customers order by random() limit 1",
        )
        return {"customer_id": customer_id} if customer_id is not None else {}

    if mutation_name in {"update-order", "delete-order", "backdate-update"}:
        order_id = _select_one_value(
            conn,
            "select order_id from shop.orders order by random() limit 1",
        )
        return {"order_id": order_id} if order_id is not None else {}

    if mutation_name == "soft-delete-order":
        order_id = _select_one_value(
            conn,
            "select order_id from shop.orders where deleted_at is null order by random() limit 1",
        )
        return {"order_id": order_id} if order_id is not None else {}

    if mutation_name == "restore-order":
        order_id = _select_one_value(
            conn,
            "select order_id from shop.orders where deleted_at is not null order by random() limit 1",
        )
        return {"order_id": order_id} if order_id is not None else {}

    if mutation_name == "delete-customer-cascade":
        customer_id = _select_one_value(
            conn,
            """
            select c.customer_id
            from shop.customers c
            join shop.orders o on o.customer_id = c.customer_id
            group by c.customer_id
            order by random()
            limit 1
            """,
        )
        return {"customer_id": customer_id} if customer_id is not None else {}

    return {}


def _build_mutation_queries(mutation_name: str, ctx: Dict, label: str) -> Dict[str, Tuple[str, Tuple]]:
    """Build context-aware queries so the observer prints the row actually changed."""
    is_before = "BEFORE" in label.upper()
    customer_id = ctx.get("customer_id")
    order_id = ctx.get("order_id")

    if mutation_name == "insert-customer":
        return {
            "customers": (
                "SELECT customer_id, name, email, country_code, created_at, updated_at FROM shop.customers ORDER BY customer_id DESC LIMIT 1",
                (),
            ),
            "dim_customers": (
                "SELECT customer_id, customer_name, email, country_code FROM analytics.dim_customers ORDER BY customer_id DESC LIMIT 1",
                (),
            ),
        }

    if mutation_name == "update-customer" and customer_id is not None:
        return {
            "customers": (
                "SELECT customer_id, name, email, country_code, created_at, updated_at FROM shop.customers WHERE customer_id = %s",
                (customer_id,),
            ),
            "dim_customers": (
                "SELECT customer_id, customer_name, email, country_code FROM analytics.dim_customers WHERE customer_id = %s",
                (customer_id,),
            ),
        }

    if mutation_name == "insert-order":
        if is_before and customer_id is not None:
            return {
                "customer_for_new_order": (
                    "SELECT customer_id, name, email, country_code FROM shop.customers WHERE customer_id = %s",
                    (customer_id,),
                ),
                "orders_for_customer": (
                    "SELECT order_id, customer_id, order_date, amount, status, deleted_at FROM shop.orders WHERE customer_id = %s ORDER BY order_id DESC LIMIT 3",
                    (customer_id,),
                ),
            }
        if order_id is not None:
            return {
                "orders": (
                    "SELECT order_id, customer_id, order_date, amount, status, created_at, updated_at, deleted_at FROM shop.orders WHERE order_id = %s",
                    (order_id,),
                ),
                "fct_orders": (
                    "SELECT order_id, customer_id, order_date, amount, status, is_paid, is_refunded, recognized_revenue FROM analytics.fct_orders WHERE order_id = %s",
                    (order_id,),
                ),
            }

    if mutation_name == "update-order" and order_id is not None:
        return {
            "orders": (
                "SELECT order_id, customer_id, amount, status, created_at, updated_at, deleted_at FROM shop.orders WHERE order_id = %s",
                (order_id,),
            ),
            "fct_orders": (
                "SELECT order_id, customer_id, amount, status, is_paid, is_refunded, recognized_revenue FROM analytics.fct_orders WHERE order_id = %s",
                (order_id,),
            ),
        }

    if mutation_name == "delete-order" and order_id is not None:
        return {
            "orders": (
                "SELECT order_id, customer_id, amount, status, deleted_at FROM shop.orders WHERE order_id = %s",
                (order_id,),
            ),
            "fct_orders": (
                "SELECT order_id, customer_id, amount, status, recognized_revenue FROM analytics.fct_orders WHERE order_id = %s",
                (order_id,),
            ),
        }

    if mutation_name == "soft-delete-order" and order_id is not None:
        return {
            "orders": (
                "SELECT order_id, customer_id, amount, status, deleted_at, updated_at FROM shop.orders WHERE order_id = %s",
                (order_id,),
            ),
            "fct_orders": (
                "SELECT order_id, customer_id, amount, status, recognized_revenue FROM analytics.fct_orders WHERE order_id = %s",
                (order_id,),
            ),
        }

    if mutation_name == "restore-order" and order_id is not None:
        return {
            "orders": (
                "SELECT order_id, customer_id, amount, status, deleted_at, updated_at FROM shop.orders WHERE order_id = %s",
                (order_id,),
            ),
            "fct_orders": (
                "SELECT order_id, customer_id, amount, status, recognized_revenue FROM analytics.fct_orders WHERE order_id = %s",
                (order_id,),
            ),
        }

    if mutation_name == "delete-customer-cascade" and customer_id is not None:
        return {
            "customer": (
                "SELECT customer_id, name, email, country_code FROM shop.customers WHERE customer_id = %s",
                (customer_id,),
            ),
            "orders_for_customer": (
                "SELECT order_id, customer_id, amount, status, deleted_at FROM shop.orders WHERE customer_id = %s ORDER BY order_id",
                (customer_id,),
            ),
            "fct_orders_for_customer": (
                "SELECT order_id, customer_id, amount, status, recognized_revenue FROM analytics.fct_orders WHERE customer_id = %s ORDER BY order_id",
                (customer_id,),
            ),
        }

    if mutation_name == "late-arriving-order":
        if is_before and customer_id is not None:
            return {
                "customer_for_late_order": (
                    "SELECT customer_id, name, email, country_code FROM shop.customers WHERE customer_id = %s",
                    (customer_id,),
                )
            }
        if order_id is not None:
            return {
                "orders": (
                    "SELECT order_id, customer_id, order_date, amount, status, created_at, updated_at FROM shop.orders WHERE order_id = %s",
                    (order_id,),
                ),
                "fct_orders": (
                    "SELECT order_id, customer_id, order_date, amount, status, recognized_revenue FROM analytics.fct_orders WHERE order_id = %s",
                    (order_id,),
                ),
            }

    if mutation_name == "backdate-update" and order_id is not None:
        return {
            "orders": (
                "SELECT order_id, customer_id, order_date, amount, status, updated_at, deleted_at FROM shop.orders WHERE order_id = %s",
                (order_id,),
            ),
            "fct_orders": (
                "SELECT order_id, customer_id, order_date, amount, status FROM analytics.fct_orders WHERE order_id = %s",
                (order_id,),
            ),
        }

    return {
        "fallback": (
            "SELECT 'No context-aware query available for this mutation yet' AS message",
            (),
        )
    }


MUTATION_GROUPS = {
    "Normal Operations": {
        "insert-customer": mutate_module.insert_customer,
        "insert-order": mutate_module.insert_order,
        "update-customer": mutate_module.update_customer,
        "update-order": mutate_module.update_order,
        "delete-order": mutate_module.delete_order,
        "delete-customer-cascade": mutate_module.delete_customer_cascade,
    },
    "Soft Delete & Restore": {
        "soft-delete-order": mutate_module.soft_delete_order,
        "restore-order": mutate_module.restore_order,
    },
    "Advanced Patterns": {
        "late-arriving-order": mutate_module.late_arriving_order,
        "backdate-update": mutate_module.backdate_update,
    },
}


# ============================================================================
# Observation Utilities
# ============================================================================

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_subsection(title):
    """Print a formatted subsection header."""
    print(f"\n{title}")
    print("-" * len(title))


def format_value(val):
    """Format a value for display."""
    if val is None:
        return "NULL"
    elif isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    elif isinstance(val, bool):
        return "✓" if val else "✗"
    else:
        return str(val)


def observe_affected_data(conn, mutation_name: str, label: str, context: Optional[Dict] = None):
    """Query and display affected rows from mutation."""
    print_subsection(f"📊 {label}")

    context = context or {}
    queries = _build_mutation_queries(mutation_name, context, label)
    
    with conn.cursor() as cur:
        for table_name, query_spec in queries.items():
            try:
                if isinstance(query_spec, tuple):
                    query_sql, params = query_spec
                else:
                    query_sql, params = query_spec, ()
                cur.execute(query_sql, params)
                rows = cur.fetchall()
                col_names = [desc[0] for desc in cur.description]
                
                if rows:
                    print(f"\n  📌 {table_name}:")
                    for i, row in enumerate(rows, 1):
                        if len(rows) > 1:
                            print(f"     [{i}]")
                        for col_name, val in zip(col_names, row):
                            print(f"       {col_name}: {format_value(val)}")
                else:
                    print(f"\n  📌 {table_name}: (no rows affected)")
                    
            except Exception as e:
                print(f"\n  📌 {table_name}: ⚠️ {str(e)[:60]}")


def run_dbt_build():
    """Run a full-refresh dbt build in the ecommerce directory."""
    print_subsection("🏗️  Running dbt build (full-refresh)...")
    
    ecommerce_dir = os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "ecommerce"
    )
    
    try:
        result = subprocess.run(
            ["bash", "-c", 
             "source ../.venv/bin/activate && dbt build --full-refresh --profiles-dir ~/.dbt --quiet"],
            cwd=ecommerce_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("  ✅ dbt build completed successfully")
            return True
        else:
            print(f"  ❌ dbt build failed:")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("  ⏱️  dbt build timed out (300s)")
        return False
    except Exception as e:
        print(f"  ❌ Error running dbt build: {str(e)}")
        return False


def apply_mutation(conn, mutation_func, mutation_context: Optional[Dict] = None):
    """Apply a single mutation."""
    print_subsection(f"🔄 Applying mutation: {mutation_func.__name__}")
    try:
        # Ensure search_path is set to shop schema for unqualified table references
        with conn.cursor() as cur:
            cur.execute("SET search_path = shop, public")

        mutation_context = mutation_context or {}
        result_context = mutation_func(conn, **mutation_context)
        conn.commit()
        return result_context or {}
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Error: {str(e)}")
        return None


def prompt_continue():
    """Prompt user to continue or exit."""
    print("\n" + "-" * 80)
    response = input("Press ENTER to continue (or 'q' to quit): ").strip().lower()
    return response != 'q'


# ============================================================================
# Interactive Mode
# ============================================================================

def mutation_requires_action(conn, mutation_name):
    """Return the prerequisite action if the mutation is not currently eligible."""
    if mutation_name in {"insert-customer"}:
        return None
    if mutation_name in {"insert-order", "update-customer", "late-arriving-order"}:
        return None if _has_customers(conn) else "insert-customer"
    if mutation_name in {"update-order", "delete-order", "backdate-update"}:
        return None if _has_orders(conn) else "insert-order"
    if mutation_name == "delete-customer-cascade":
        return None if _has_customer_with_orders(conn) else "insert-order"
    if mutation_name == "soft-delete-order":
        return None if _has_active_orders(conn) else "insert-order"
    if mutation_name == "restore-order":
        return None if _has_deleted_orders(conn) else "soft-delete-order"
    return None


def show_mutation_menu(conn):
    """Display mutation options and return selected mutation."""
    print_section("AVAILABLE MUTATIONS")
    
    all_mutations = {}
    option_num = 1
    
    for group_name, mutations in MUTATION_GROUPS.items():
        print(f"\n{group_name}:")
        for mutation_name in mutations.keys():
            prerequisite = mutation_requires_action(conn, mutation_name)
            if prerequisite is not None:
                print(f"  {option_num:2d}. {mutation_name}  (needs: {prerequisite})")
            else:
                print(f"  {option_num:2d}. {mutation_name}")
            all_mutations[option_num] = (mutation_name, mutations[mutation_name], prerequisite)
            option_num += 1
    
    print(f"\n  {'r':>2}. Random mutation")
    print(f"  {'q':>2}. Quit")

    print("\nAdvanced patterns help:")
    print("  - late-arriving-order: creates a new order now with an old order_date")
    print("    to simulate delayed ingestion from an upstream system.")
    print("  - backdate-update: edits an existing order but sets updated_at to the past")
    print("    to show how naive incremental filters can miss changed rows.")
    
    while True:
        try:
            choice = input("\nSelect option: ").strip().lower()
            
            if choice == 'q':
                return None
            elif choice == 'r':
                eligible = [(name, func) for _, (name, func, prereq) in all_mutations.items() if prereq is None]
                if not eligible:
                    print("\n  ℹ️  No valid random mutation is available right now. Run 'insert-customer' first.")
                    return None
                mutation_name, mutation_func = random.choice(eligible)
                print(f"\n  🎲 Random: {mutation_name}")
                return mutation_func
            else:
                choice_num = int(choice)
                if choice_num in all_mutations:
                    _, mutation_func, prereq = all_mutations[choice_num]
                    if prereq is not None:
                        print(f"\n  ℹ️  This action requires a prior step: '{prereq}'.")
                        continue
                    return mutation_func
                else:
                    print("  ❌ Invalid choice")
        except ValueError:
            print("  ❌ Please enter a valid number")


def interactive_mode():
    """Run in interactive mode: observe → mutate → build → repeat."""
    print_section("🔍 PROGRESSIVE DATA MUTATION OBSERVER")
    
    with psycopg.connect(DSN) as conn:
        iteration = 1
        
        while True:
            print_section(f"ITERATION {iteration}")
            
            # Step 1: Choose mutation
            mutation_func = show_mutation_menu(conn)
            if mutation_func is None:
                print_section("👋 GOODBYE")
                break
            
            mutation_name = mutation_func.__name__
            mutation_name_hyphen = mutation_name.replace("_", "-")
            mutation_context = _prepare_mutation_context(conn, mutation_name_hyphen)
            
            # Step 2: Observe affected data before
            observe_affected_data(
                conn,
                mutation_name_hyphen,
                label="BEFORE MUTATION",
                context=mutation_context,
            )
            
            # Step 3: Apply mutation
            mutation_result_context = apply_mutation(conn, mutation_func, mutation_context)
            if mutation_result_context is None:
                if not prompt_continue():
                    print_section("👋 GOODBYE")
                    break
                iteration += 1
                continue

            merged_context = {**mutation_context, **mutation_result_context}
            
            # Step 4: Run dbt build
            time.sleep(1)  # Small delay for DB consistency
            dbt_success = run_dbt_build()
            
            # Step 5: Observe affected data after
            observe_affected_data(
                conn,
                mutation_name_hyphen,
                label="AFTER MUTATION + dbt build",
                context=merged_context,
            )
            
            # Step 6: Prompt for next iteration
            if not prompt_continue():
                print_section("👋 GOODBYE")
                break
            
            iteration += 1


def single_mutation_mode(action):
    """Run a single mutation and always build dependent tables."""
    print_section(f"🔍 SINGLE MUTATION: {action}")
    
    # Find mutation function
    mutation_func = None
    for group_mutations in MUTATION_GROUPS.values():
        if action in group_mutations:
            mutation_func = group_mutations[action]
            break
    
    if mutation_func is None:
        print(f"❌ Unknown mutation: {action}")
        sys.exit(1)
    
    with psycopg.connect(DSN) as conn:
        mutation_context = _prepare_mutation_context(conn, action)

        # Observe before
        observe_affected_data(conn, action, label="BEFORE MUTATION", context=mutation_context)
        
        # Apply mutation
        mutation_result_context = apply_mutation(conn, mutation_func, mutation_context)
        if mutation_result_context is None:
            sys.exit(1)

        merged_context = {**mutation_context, **mutation_result_context}
        
        print("\n✅ Mutation applied")
        
        # Always run dbt build so every downstream table is updated.
        time.sleep(1)
        run_dbt_build()

        # Observe after
        observe_affected_data(conn, action, label="AFTER MUTATION + dbt build", context=merged_context)


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Interactive progressive mutation observer"
    )
    parser.add_argument(
        "--action",
        help="Run specific mutation (skip interactive mode)"
    )
    
    args = parser.parse_args()
    
    if args.action:
        single_mutation_mode(args.action)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
