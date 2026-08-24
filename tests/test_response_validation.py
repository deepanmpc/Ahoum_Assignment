"""Tests for response parsing and validation (D4)."""

import pytest
import json

from ahoum_assignment.response_parser import extract_json
from ahoum_assignment.response_validator import validate_batch_response


def test_valid_json():
    payload = json.dumps({"results": [{
        "facet_id": "f1", "status": "scored", "score_1_to_5": 4,
        "confidence_0_to_1": 0.85, "evidence_quote": "I waited calmly",
        "reason": "Direct evidence of patience",
    }]})
    result = validate_batch_response(payload, ["f1"], "I waited calmly in line.")
    assert result.success
    assert len(result.items) == 1


def test_fenced_json():
    payload = '```json\n{"results": [{"facet_id": "f1", "status": "insufficient_evidence", "score_1_to_5": null, "confidence_0_to_1": 0.2, "evidence_quote": "", "reason": "No evidence"}]}\n```'
    result = validate_batch_response(payload, ["f1"], "text")
    assert result.success


def test_prose_plus_json():
    payload = 'Here is the analysis:\n\n{"results": [{"facet_id": "f1", "status": "insufficient_evidence", "score_1_to_5": null, "confidence_0_to_1": 0.1, "evidence_quote": "", "reason": "None found"}]}\n\nHope this helps!'
    result = validate_batch_response(payload, ["f1"], "text")
    assert result.success


def test_malformed_json():
    result = validate_batch_response("{bad json!!!}", ["f1"], "text")
    assert not result.success
    assert "Could not extract" in result.errors[0]


def test_missing_facet_id():
    payload = json.dumps({"results": [{
        "facet_id": "f1", "status": "scored", "score_1_to_5": 3,
        "confidence_0_to_1": 0.7, "evidence_quote": "text", "reason": "r",
    }]})
    result = validate_batch_response(payload, ["f1", "f2"], "text is here")
    assert not result.success
    assert any("Missing" in e for e in result.errors)


def test_duplicate_facet_id():
    payload = json.dumps({"results": [
        {"facet_id": "f1", "status": "scored", "score_1_to_5": 3,
         "confidence_0_to_1": 0.7, "evidence_quote": "x", "reason": "r"},
        {"facet_id": "f1", "status": "scored", "score_1_to_5": 4,
         "confidence_0_to_1": 0.8, "evidence_quote": "x", "reason": "r"},
    ]})
    result = validate_batch_response(payload, ["f1"], "x is present")
    assert not result.success
    assert any("Duplicate" in e for e in result.errors)


def test_extra_facet_id():
    payload = json.dumps({"results": [
        {"facet_id": "f1", "status": "scored", "score_1_to_5": 3,
         "confidence_0_to_1": 0.7, "evidence_quote": "x", "reason": "r"},
        {"facet_id": "f_unknown", "status": "scored", "score_1_to_5": 3,
         "confidence_0_to_1": 0.7, "evidence_quote": "x", "reason": "r"},
    ]})
    result = validate_batch_response(payload, ["f1"], "x is present")
    assert not result.success
    assert any("Extra" in e for e in result.errors)


def test_invalid_score_zero():
    payload = json.dumps({"results": [{
        "facet_id": "f1", "status": "scored", "score_1_to_5": 0,
        "confidence_0_to_1": 0.7, "evidence_quote": "x", "reason": "r",
    }]})
    result = validate_batch_response(payload, ["f1"], "x")
    assert not result.success


def test_abstention_with_score():
    payload = json.dumps({"results": [{
        "facet_id": "f1", "status": "insufficient_evidence", "score_1_to_5": 3,
        "confidence_0_to_1": 0.5, "evidence_quote": "", "reason": "r",
    }]})
    result = validate_batch_response(payload, ["f1"], "text")
    assert not result.success


def test_confidence_outside_range():
    payload = json.dumps({"results": [{
        "facet_id": "f1", "status": "scored", "score_1_to_5": 4,
        "confidence_0_to_1": 1.5, "evidence_quote": "x", "reason": "r",
    }]})
    result = validate_batch_response(payload, ["f1"], "x")
    assert not result.success


def test_invented_evidence_quote():
    payload = json.dumps({"results": [{
        "facet_id": "f1", "status": "scored", "score_1_to_5": 4,
        "confidence_0_to_1": 0.9, "evidence_quote": "I am very happy today",
        "reason": "Direct evidence",
    }]})
    # conversation does NOT contain "I am very happy today"
    result = validate_batch_response(payload, ["f1"], "The weather is nice.")
    assert not result.success
    assert any("not found in conversation" in e for e in result.errors)
