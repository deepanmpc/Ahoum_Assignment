import pytest

from ahoum_assignment.contracts import FacetScore, ScoreStatus


def test_scored_result_requires_valid_ordinal_score() -> None:
    result = FacetScore(
        facet_id="facet-001",
        facet_raw="Patience",
        facet_normalized="patience",
        status=ScoreStatus.SCORED,
        score_1_to_5=4,
        confidence_0_to_1=0.75,
        evidence="I waited calmly.",
        reason="Direct self-report of calm waiting.",
    )
    assert result.score_1_to_5 == 4


@pytest.mark.parametrize("status", [ScoreStatus.INSUFFICIENT_EVIDENCE, ScoreStatus.NOT_OBSERVABLE])
def test_abstention_cannot_contain_a_numeric_score(status: ScoreStatus) -> None:
    with pytest.raises(ValueError, match="must not contain a numeric score"):
        FacetScore(
            facet_id="facet-001",
            facet_raw="Patience",
            facet_normalized="patience",
            status=status,
            score_1_to_5=3,
            confidence_0_to_1=0.8,
            evidence="",
            reason="The conversation does not provide enough evidence.",
        )
