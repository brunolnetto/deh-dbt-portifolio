"""SODA Core quality checks for landing tables."""
import os

import pytest

from .conftest import SODA_CHECKS_DIR, SODA_CONFIG


def _scan(checks_file: str) -> None:
    from soda.scan import Scan

    scan = Scan()
    scan.set_data_source_name("landing")
    scan.add_configuration_yaml_file(SODA_CONFIG)
    scan.add_sodacl_yaml_file(checks_file)
    scan.execute()

    errors = scan.get_error_logs()
    assert not errors, f"SODA scan errors:\n" + "\n".join(str(e) for e in errors)

    failed = [c for c in scan.get_checks() if str(c.outcome) == "fail"]
    assert not failed, "SODA checks failed:\n" + "\n".join(str(c) for c in failed)


def test_soda_varejo():
    _scan(os.path.join(SODA_CHECKS_DIR, "varejo.yml"))


def test_soda_biblioteca():
    _scan(os.path.join(SODA_CHECKS_DIR, "biblioteca.yml"))


def test_soda_rede_social():
    _scan(os.path.join(SODA_CHECKS_DIR, "rede_social.yml"))
