#!/usr/bin/env python3
"""
observe.py - Interactive progressive data mutation and observation tool.

Allows you to:
1. View the current state (OLTP, staging, marts)
2. Apply a mutation (insert, update, delete, bugs)
3. Run dbt build automatically
4. Compare before/after state
5. Repeat for next observation

Usage:
    python observe.py              # Interactive mode
    python observe.py --action insert-customer  # Run specific mutation
    python observe.py --skip-dbt insert-order   # Skip dbt build
"""

import argparse
import subprocess
import sys
import os
from datetime import datetime, timedelta
import random
import time

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

# ============================================================================
# Observation Queries
# ============================================================================

OBSERVATION_QUERIES = {
    "orders_summary": """
        SELECT 
            COUNT(*) as total_orders,
            COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_orders,
            COUNT(CASE WHEN deleted_at IS NOT NULL THEN 1 END) as deleted_orders,
            COUNT(DISTINCT customer_id) as customers_with_orders,
            MAX(updated_at) as last_update
        FROM shop.orders;
    """,
    
    "customers_summary": """
        SELECT 
            COUNT(*) as total_customers,
            COUNT(DISTINCT country_code) as countries,
            COUNT(DISTINCT email) as unique_emails,
            MAX(updated_at) as last_update
        FROM shop.customers;
    """,
    
    "fct_orders_count": """
        SELECT 
            COUNT(*) as fct_orders_count,
            COUNT(CASE WHEN is_paid = 1 THEN 1 END) as paid_count,
            COUNT(CASE WHEN is_refunded = 1 THEN 1 END) as refunded_count,
            SUM(recognized_revenue) as total_revenue
        FROM analytics.fct_orders;
    """,
    
    "mart_customer_sales_count": """
        SELECT 
            COUNT(*) as customer_count,
            SUM(total_orders) as total_orders,
            SUM(revenue) as total_revenue
        FROM analytics.mart_customer_sales;
    """,
    
    "dim_customers_count": """
        SELECT 
            COUNT(*) as dim_customers_count,
            COUNT(DISTINCT country_code) as countries
        FROM analytics.dim_customers;
    """,
}

MUTATION_GROUPS = {
    "Normal Operations": {
        "insert-customer": mutate_module.insert_customer,
        "insert-order": mutate_module.insert_order,
        "update-customer": mutate_module.update_customer,
        "update-order": mutate_module.update_order,
    },
    "Soft Delete & Restore": {
        "soft-delete-order": mutate_module.soft_delete_order,
        "restore-order": mutate_module.restore_order,
    },
    "Advanced Patterns": {
        "late-arriving-order": mutate_module.late_arriving_order,
        "backdate-update": mutate_module.backdate_update,
    },
    "Data Quality Issues": {
        "bug-invalid-country": mutate_module.bug_invalid_country,
        "bug-negative-amount": mutate_module.bug_negative_amount,
        "bug-zero-amount": mutate_module.bug_zero_amount,
        "bug-future-order": mutate_module.bug_future_order,
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


def observe_state(conn, label="STATE"):
    """Query and print current data state."""
    print_subsection(f"📊 {label}")
    
    with conn.cursor() as cur:
        for query_name, query_sql in OBSERVATION_QUERIES.items():
            try:
                cur.execute(query_sql)
                result = cur.fetchone()
                col_names = [desc[0] for desc in cur.description]
                
                print(f"\n  {query_name}:")
                for name, value in zip(col_names, result):
                    print(f"    • {name}: {value}")
            except Exception as e:
                print(f"  ⚠️  {query_name}: {str(e)[:60]}")


def run_dbt_build():
    """Run dbt build in the ecommerce directory."""
    print_subsection("🏗️  Running dbt build...")
    
    ecommerce_dir = os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "ecommerce"
    )
    
    try:
        result = subprocess.run(
            ["bash", "-c", 
             "source ../.venv/bin/activate && dbt build --profiles-dir ~/.dbt --quiet"],
            cwd=ecommerce_dir,
            capture_output=True,
            text=True,
            timeout=120
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
        print("  ⏱️  dbt build timed out (120s)")
        return False
    except Exception as e:
        print(f"  ❌ Error running dbt build: {str(e)}")
        return False


def apply_mutation(conn, mutation_func):
    """Apply a single mutation."""
    print_subsection(f"🔄 Applying mutation: {mutation_func.__name__}")
    try:
        mutation_func(conn)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Error: {str(e)}")
        return False


def prompt_continue():
    """Prompt user to continue or exit."""
    print("\n" + "-" * 80)
    response = input("Press ENTER to continue (or 'q' to quit): ").strip().lower()
    return response != 'q'


# ============================================================================
# Interactive Mode
# ============================================================================

def show_mutation_menu():
    """Display mutation options and return selected mutation."""
    print_section("AVAILABLE MUTATIONS")
    
    all_mutations = {}
    option_num = 1
    
    for group_name, mutations in MUTATION_GROUPS.items():
        print(f"\n{group_name}:")
        for mutation_name in mutations.keys():
            print(f"  {option_num:2d}. {mutation_name}")
            all_mutations[option_num] = (mutation_name, mutations[mutation_name])
            option_num += 1
    
    print(f"\n  {'r':>2}. Random mutation")
    print(f"  {'q':>2}. Quit")
    
    while True:
        try:
            choice = input("\nSelect option: ").strip().lower()
            
            if choice == 'q':
                return None
            elif choice == 'r':
                mutation_name, mutation_func = random.choice(list(all_mutations.values()))
                print(f"\n  🎲 Random: {mutation_name}")
                return mutation_func
            else:
                choice_num = int(choice)
                if choice_num in all_mutations:
                    _, mutation_func = all_mutations[choice_num]
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
            
            # Step 1: Observe current state
            observe_state(conn, label="BEFORE MUTATION")
            
            # Step 2: Choose mutation
            mutation_func = show_mutation_menu()
            if mutation_func is None:
                print_section("👋 GOODBYE")
                break
            
            # Step 3: Apply mutation
            if not apply_mutation(conn, mutation_func):
                continue
            
            print("\n  Mutation applied and committed")
            
            # Step 4: Run dbt build
            time.sleep(1)  # Small delay for DB consistency
            dbt_success = run_dbt_build()
            
            # Step 5: Observe new state
            observe_state(conn, label="AFTER MUTATION + dbt build")
            
            # Step 6: Prompt for next iteration
            if not prompt_continue():
                print_section("👋 GOODBYE")
                break
            
            iteration += 1


def single_mutation_mode(action, skip_dbt=False):
    """Run a single mutation and optionally build."""
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
        # Observe before
        observe_state(conn, label="BEFORE MUTATION")
        
        # Apply mutation
        if not apply_mutation(conn, mutation_func):
            sys.exit(1)
        
        print("\n✅ Mutation applied")
        
        # Run dbt build if not skipped
        if not skip_dbt:
            time.sleep(1)
            run_dbt_build()
            
            # Observe after
            observe_state(conn, label="AFTER MUTATION + dbt build")
        else:
            print("⏭️  Skipped dbt build (use --skip-dbt)")


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
    parser.add_argument(
        "--skip-dbt",
        action="store_true",
        help="Don't run dbt build after mutation"
    )
    
    args = parser.parse_args()
    
    if args.action:
        single_mutation_mode(args.action, skip_dbt=args.skip_dbt)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
