"""Regression tests for API life tables and integrity verification."""
import pytest
from fastapi import HTTPException

from agents.api import LifeTableRequest, api_lifetable
from agents.base import AuditTrail


def test_life_table_api_validates_mortality_input():
    request = LifeTableRequest(intervals=[
        {"age": 0, "mx": 0.02},
        {"age": 5, "mx": 0.02},
    ])
    response = api_lifetable(request)
    assert response["life_expectancy"] == pytest.approx(50)
    assert response["table"][-1]["qx"] == 1
    with pytest.raises(HTTPException) as exc:
        api_lifetable(LifeTableRequest(intervals=[{"age": 0, "mx": 0}]))
    assert exc.value.status_code == 422


def test_audit_verifier_detects_content_tampering():
    trail = AuditTrail(secret_key="fixed-test-key")
    trail.log("tester", "test", "event", {"value": 1})
    trail.log("tester", "test", "event", {"value": 2})
    assert trail.verify_integrity()
    exported = trail.get_trail()
    exported[0]["actor"] = "forged"
    assert trail.verify_integrity()  # exported list does not mutate internal ledger
    trail.logs[0]["actor"] = "forged"
    assert not trail.verify_integrity()


def test_audit_verifier_detects_payload_hash_tampering():
    trail = AuditTrail(secret_key="fixed-test-key")
    trail.log("tester", "test", "event", {"value": 1})
    trail.logs[0]["payload_hash"] = "0" * 64
    assert not trail.verify_integrity()
