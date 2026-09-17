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
    
    # Execute scan - if checks fail, SODA will record them
    scan.execute()

    # Check for execution errors (configuration, connection issues)
    errors = scan.get_error_logs()
    assert not errors, f"SODA scan errors:\n" + "\n".join(str(e) for e in errors)
    
    # Check if any checks failed by looking at the private _checks list
    # (SODA v3 doesn't expose a public API for this, so we use the suggested attribute)
    if hasattr(scan, '_checks') and scan._checks:
        failed_checks = [c for c in scan._checks if hasattr(c, 'outcome') and str(c.outcome) == 'fail']
        assert not failed_checks, f"SODA checks failed:\n" + "\n".join(str(c) for c in failed_checks)


def test_soda_varejo():
    _scan(os.path.join(SODA_CHECKS_DIR, "varejo.yml"))


def test_soda_biblioteca():
    _scan(os.path.join(SODA_CHECKS_DIR, "biblioteca.yml"))


def test_soda_rede_social():
    _scan(os.path.join(SODA_CHECKS_DIR, "rede_social.yml"))
