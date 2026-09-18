FROM astrocrpublic.azurecr.io/runtime:3.0-2

# Airflow itself never runs dbt — Cosmos only *parses* a pre-generated
# manifest.json here (LoadMode.DBT_MANIFEST) and dispatches every dbt node to a
# disposable container built from include/dbt_runner/Dockerfile
# (ExecutionMode.DOCKER). See dags/dbt_transform_dag.py.
