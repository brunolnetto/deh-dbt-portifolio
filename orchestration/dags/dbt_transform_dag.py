"""Cosmos DAG — runs the portifolio/ dbt project as containerized tasks.

Rendering (building the Airflow task graph) uses a pre-generated manifest.json
(LoadMode.DBT_MANIFEST) so the Airflow worker never needs dbt installed —
regenerate it whenever the dbt project changes:

    make dbt-manifest

Execution of every dbt node (run/test/snapshot) happens inside a disposable
sibling container built from include/dbt_runner/Dockerfile
(ExecutionMode.DOCKER), keeping the Airflow image itself dbt-free and every
transformation reproducible/isolated. See orchestration/README.md for the
docker.sock + shared-network setup this relies on.
"""
import os
from pathlib import Path

from cosmos import DbtDag, ExecutionConfig, ProfileConfig, ProjectConfig, RenderConfig
from cosmos.constants import ExecutionMode, LoadMode
from pendulum import datetime

# Mounted read-only into the scheduler by docker-compose.override.yml — used
# only for parsing (manifest + profile name/target), not for execution.
_INCLUDE_DIR = Path("/usr/local/airflow/include/portifolio")

# Path baked into the dbt_runner image (see include/dbt_runner/Dockerfile) —
# this is where each spawned container actually runs `dbt`.
_CONTAINER_PROJECT_DIR = "/usr/app/portifolio"

DBT_RUNNER_IMAGE = os.getenv("DBT_RUNNER_IMAGE", "deh-dbt-runner:latest")
DEH_NETWORK = os.getenv("DEH_DOCKER_NETWORK", "deh_network")

project_config = ProjectConfig(
    dbt_project_path=_CONTAINER_PROJECT_DIR,
    manifest_path=_INCLUDE_DIR / "target" / "manifest.json",
    project_name="portfolio",
)

profile_config = ProfileConfig(
    profile_name="portfolio",
    target_name="dev",
    profiles_yml_filepath=_INCLUDE_DIR / "profiles.yml",
)

render_config = RenderConfig(load_method=LoadMode.DBT_MANIFEST)

execution_config = ExecutionConfig(execution_mode=ExecutionMode.DOCKER)

operator_args = {
    "image": DBT_RUNNER_IMAGE,
    "network_mode": DEH_NETWORK,
    "auto_remove": "success",
    "environment": {
        "POSTGRES_HOST": os.getenv("POSTGRES_HOST", "postgres"),
        "POSTGRES_PORT": os.getenv("POSTGRES_PORT", "5432"),
        "POSTGRES_USER": os.getenv("POSTGRES_USER", "dbt"),
        "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", "dbt"),
        "POSTGRES_DB": os.getenv("POSTGRES_DB", "portifolio"),
    },
}

dbt_transform_dag = DbtDag(
    dag_id="dbt_transform",
    project_config=project_config,
    profile_config=profile_config,
    render_config=render_config,
    execution_config=execution_config,
    operator_args=operator_args,
    schedule="@hourly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"retries": 1},
    tags=["dbt", "cosmos", "transform"],
)
