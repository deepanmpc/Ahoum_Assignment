import pytest
from ahoum_assignment.anchor_rules import apply_anchors


def test_observable_gets_anchors():
    rec = {
        "facet_normalized": "patience", 
        "conversation_observable": "true", 
        "facet_type": "conversational_trait"
    }
    res = apply_anchors(rec, overrides={})
    assert res["scoring_definition"] != ""
    assert res["anchor_1"] != ""
    assert res["anchor_3"] != ""
    assert res["anchor_5"] != ""
    assert "patience" in res["anchor_3"]


def test_non_observable_unanchored():
    rec = {
        "facet_normalized": "fsh level", 
        "conversation_observable": "false", 
        "facet_type": "medical_or_diagnostic"
    }
    res = apply_anchors(rec, overrides={})
    assert res["scoring_definition"] == ""
    assert res["anchor_1"] == ""
    assert res["anchor_5"] == ""


def test_uncertain_unanchored():
    rec = {
        "facet_normalized": "unknown trait", 
        "conversation_observable": "uncertain", 
        "facet_type": "unclear_or_malformed"
    }
    res = apply_anchors(rec, overrides={})
    assert res["scoring_definition"] == ""
    assert res["anchor_1"] == ""


def test_overrides_applied():
    rec = {
        "facet_normalized": "test_trait", 
        "conversation_observable": "true"
    }
    overrides = {
        "test_trait": {
            "scoring_definition": "Override Def",
            "anchor_1": "Override 1",
            "anchor_3": "Override 3",
            "anchor_5": "Override 5"
        }
    }
    res = apply_anchors(rec, overrides)
    assert res["scoring_definition"] == "Override Def"
    assert res["anchor_1"] == "Override 1"
    assert res["anchor_5"] == "Override 5"
