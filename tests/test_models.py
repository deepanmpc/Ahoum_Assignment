import pytest
from pydantic import ValidationError
from ahoum_assignment.models import FacetScore, ScoreStatus


def test_valid_scored_result():
    score = FacetScore(
        facet_id="f1",
        facet_raw="Risktaking",
        facet_normalized="risk_taking",
        status=ScoreStatus.SCORED,
        score_1_to_5=4,
        confidence_0_to_1=0.85,
        evidence="User literally said they love taking big bets.",
        reason="Clear indication of risk taking behavior."
    )
    assert score.score_1_to_5 == 4
    assert score.status == ScoreStatus.SCORED


def test_insufficient_evidence_with_score_fails():
    with pytest.raises(ValidationError) as exc:
        FacetScore(
            facet_id="f2",
            facet_raw="Naivety",
            facet_normalized="naivety",
            status=ScoreStatus.INSUFFICIENT_EVIDENCE,
            score_1_to_5=3,  # Should not have a score
            confidence_0_to_1=0.9,
            reason="Not enough context to determine naivety."
        )
    assert "cannot have a numeric score" in str(exc.value)


def test_not_observable_with_score_fails():
    with pytest.raises(ValidationError) as exc:
        FacetScore(
            facet_id="f3",
            facet_raw="Blood Pressure",
            facet_normalized="blood_pressure",
            status=ScoreStatus.NOT_OBSERVABLE,
            score_1_to_5=2,  # Should not have a score
            confidence_0_to_1=1.0,
            reason="Cannot determine blood pressure from text."
        )
    assert "cannot have a numeric score" in str(exc.value)


def test_invalid_confidence_fails():
    with pytest.raises(ValidationError) as exc:
        FacetScore(
            facet_id="f4",
            facet_raw="Acidity",
            facet_normalized="acidity",
            status=ScoreStatus.SCORED,
            score_1_to_5=5,
            confidence_0_to_1=1.5,  # Invalid confidence
            reason="Clear signs of acidic behavior."
        )
    assert "Confidence must be between 0 and 1" in str(exc.value)

    with pytest.raises(ValidationError) as exc_low:
        FacetScore(
            facet_id="f4",
            facet_raw="Acidity",
            facet_normalized="acidity",
            status=ScoreStatus.SCORED,
            score_1_to_5=5,
            confidence_0_to_1=-0.1,  # Invalid confidence
            reason="Clear signs of acidic behavior."
        )
    assert "Confidence must be between 0 and 1" in str(exc_low.value)


def test_blank_reason_fails():
    with pytest.raises(ValidationError) as exc:
        FacetScore(
            facet_id="f5",
            facet_raw="Testing",
            facet_normalized="testing",
            status=ScoreStatus.INSUFFICIENT_EVIDENCE,
            score_1_to_5=None,
            confidence_0_to_1=0.5,
            reason=""  # Blank reason
        )
    assert "Field cannot be blank" in str(exc.value)

def test_blank_id_fails():
    with pytest.raises(ValidationError) as exc:
        FacetScore(
            facet_id="   ",
            facet_raw="Testing",
            facet_normalized="testing",
            status=ScoreStatus.SCORED,
            score_1_to_5=3,
            confidence_0_to_1=0.5,
            reason="valid reason"
        )
    assert "Field cannot be blank" in str(exc.value)
