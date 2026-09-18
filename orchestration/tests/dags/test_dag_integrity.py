"""Sanity checks: every DAG file must import without exceptions or import cycles."""
import os

from airflow.models import DagBag


def test_no_import_errors():
    dag_folder = os.path.join(os.path.dirname(__file__), "..", "..", "dags")
    dag_bag = DagBag(dag_folder=dag_folder, include_examples=False)
    assert not dag_bag.import_errors, f"DAG import errors: {dag_bag.import_errors}"
