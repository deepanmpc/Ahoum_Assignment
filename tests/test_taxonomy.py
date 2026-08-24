import pytest
from ahoum_assignment.taxonomy_rules import classify_facet, load_overrides


def test_medical_diagnostic_facets():
    res = classify_facet("blood pressure", is_malf=False, overrides={})
    assert res["facet_category"] == "health_medical"
    assert res["facet_type"] == "medical_or_diagnostic"
    assert res["conversation_observable"] == "false"
    assert res["sensitivity"] == "high_risk"
    assert "medical evidence" in res["abstention_reason"]
    assert res["review_required"] == "true"


def test_external_biography_facets():
    res = classify_facet("demographic age", is_malf=False, overrides={})
    assert res["facet_category"] == "biography_external"
    assert res["facet_type"] == "external_biographical_fact"
    assert res["conversation_observable"] == "false"
    assert res["sensitivity"] == "ordinary"
    assert "historical" in res["abstention_reason"]


def test_religious_practice_facets():
    res = classify_facet("pilgrimage attendance", is_malf=False, overrides={})
    assert res["facet_category"] == "religion_culture"
    assert res["facet_type"] == "religious_or_cultural_practice"
    assert res["conversation_observable"] == "false"
    assert res["sensitivity"] == "sensitive"
    assert res["review_required"] == "true"


def test_ordinary_conversational_traits():
    res = classify_facet("talkative", is_malf=False, overrides={})
    assert res["facet_category"] == "communication"
    assert res["facet_type"] == "conversational_behavior"
    assert res["conversation_observable"] == "true"
    assert res["sensitivity"] == "ordinary"
    assert res["abstention_reason"] == ""
    assert res["review_required"] == "false"


def test_unclear_facet_names():
    res = classify_facet("something entirely unknown", is_malf=False, overrides={})
    assert res["facet_category"] == "unclear"
    assert res["facet_type"] == "unclear_or_malformed"
    assert res["conversation_observable"] == "uncertain"
    assert res["sensitivity"] == "ordinary"
    assert res["review_required"] == "true"


def test_sensitive_classifications():
    # Finance/Risk falls under sensitive
    res = classify_facet("risk tolerance", is_malf=False, overrides={})
    assert res["facet_category"] == "finance_risk"
    assert res["sensitivity"] == "sensitive"
    assert res["conversation_observable"] == "uncertain"
    assert res["review_required"] == "true"


def test_manual_override():
    overrides = {
        "custom trait": {
            "facet_category": "values",
            "facet_type": "conversational_trait",
            "conversation_observable": "true",
            "observability_reason": "Manual",
            "sensitivity": "ordinary",
            "abstention_reason": "",
            "review_required": "false"
        }
    }
    res = classify_facet("custom trait", is_malf=False, overrides=overrides)
    assert res["facet_category"] == "values"
    assert res["conversation_observable"] == "true"
    assert res["review_required"] is False

def test_regression_broad_medical_rules():
    # 'subscription count' shouldn't be medical just because it has 'count'
    res = classify_facet("subscription count", is_malf=False, overrides={})
    assert res["facet_category"] == "unclear"
    
    # 'anatomy knowledge' might be unclear now, but certainly not high_risk medical 
    # without explicit clinical context.
    res = classify_facet("anatomy knowledge", is_malf=False, overrides={})
    assert res["facet_type"] != "medical_or_diagnostic"

def test_regression_broad_biography_rules():
    # 'encouraging participation' shouldn't be biography just because of 'participation'
    res = classify_facet("encouraging participation", is_malf=False, overrides={})
    assert res["facet_category"] == "unclear"
