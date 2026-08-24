import pytest
import csv
import tomllib
from pathlib import Path

from ahoum_assignment.keyword_router import KeywordRouter

@pytest.fixture
def setup_router(tmp_path: Path):
    rules_path = tmp_path / "rules.toml"
    cat_path = tmp_path / "cat.csv"
    
    rules_content = """
    [config]
    max_candidates_per_category = 2
    base_keyword_score = 0.5
    score_per_match = 0.1
    
    [categories.finance_risk]
    weight = 0.9
    keywords = ["budget", "savings", "investment risk"]
    negative_keywords = ["not my money"]
    
    [categories.health_medical]
    weight = 0.8
    keywords = ["blood pressure"]
    """
    rules_path.write_text(rules_content, encoding='utf-8')
    
    with open(cat_path, 'w', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["facet_id", "facet_raw", "facet_normalized", "facet_category", "conversation_observable"])
        writer.writeheader()
        writer.writerow({"facet_id": "f1", "facet_raw": "r1", "facet_normalized": "n1", "facet_category": "finance_risk", "conversation_observable": "true"})
        writer.writerow({"facet_id": "f2", "facet_raw": "r2", "facet_normalized": "n2", "facet_category": "finance_risk", "conversation_observable": "true"})
        writer.writerow({"facet_id": "f3", "facet_raw": "r3", "facet_normalized": "n3", "facet_category": "finance_risk", "conversation_observable": "true"})
        writer.writerow({"facet_id": "m1", "facet_raw": "rm", "facet_normalized": "nm", "facet_category": "health_medical", "conversation_observable": "false"})
        
    return KeywordRouter(rules_path, cat_path)

def test_case_insensitive_matching(setup_router):
    res = setup_router.retrieve("We need a BUDGET for the house.")
    assert res.candidate_count > 0
    assert "budget" in res.candidates[0].matched_keywords

def test_phrase_matching(setup_router):
    res = setup_router.retrieve("They took on an investment risk yesterday.")
    assert res.candidate_count > 0
    assert "investment risk" in res.candidates[0].matched_keywords

def test_negative_keyword_behavior(setup_router):
    res = setup_router.retrieve("It's not my money but I budget.")
    assert res.candidate_count == 0

def test_false_positive_prevention(setup_router):
    # 'savings' shouldn't match 'savingsaccount' without boundary
    res = setup_router.retrieve("My savingsaccount is closed.")
    assert res.candidate_count == 0

def test_excluded_medical_facets(setup_router):
    # medical has 'blood pressure', mapped to health_medical, but m1 is conversation_observable=false
    res = setup_router.retrieve("My blood pressure is high.")
    assert res.candidate_count == 0
    assert res.excluded_count > 0

def test_deterministic_ordering_and_max_cap(setup_router):
    # Only 2 per category allowed by config
    res = setup_router.retrieve("budget and savings")
    assert res.candidate_count == 2
    assert res.candidates[0].facet_id == "f1"
    assert res.candidates[1].facet_id == "f2"

def test_no_match_result(setup_router):
    res = setup_router.retrieve("Completely unrelated text about cats.")
    assert res.candidate_count == 0
    assert len(res.warnings) == 1
