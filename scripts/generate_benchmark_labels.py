import csv
import json
from pathlib import Path
from ahoum_assignment.benchmark_models import ReferenceLabel

def main():
    root = Path(__file__).resolve().parents[1]
    catalogue_path = root / "data" / "processed" / "facet_catalogue.csv"
    rep_facets_path = root / "data" / "examples" / "representative_facets.csv"
    labels_path = root / "data" / "examples" / "reference_labels.jsonl"
    
    # Selection criteria:
    # We want a mix of observable traits (communication, emotional_regulation, decision_making_risk, social_interaction, work_habits)
    # And non-observable (medical, biography, religious, unclear)
    
    selected_facets = []
    category_counts = {}
    
    with open(catalogue_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row["facet_category"]
            obs = row["conversation_observable"]
            
            # Pick a few from each category
            if category_counts.get(cat, 0) < 3:
                selected_facets.append({
                    "facet_id": row["facet_id"],
                    "facet_raw": row["facet_raw"],
                    "facet_normalized": row["facet_normalized"],
                    "facet_category": row["facet_category"],
                    "conversation_observable": row["conversation_observable"],
                    "sensitivity": "high" if cat in ["health_medical", "biography", "religion_culture"] else "normal",
                    "reason_for_benchmark": f"Representative of {cat} ({obs})"
                })
                category_counts[cat] = category_counts.get(cat, 0) + 1
                
            if len(selected_facets) >= 25:
                break
                
    with open(rep_facets_path, "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=selected_facets[0].keys())
        writer.writeheader()
        writer.writerows(selected_facets)
        
    print(f"Wrote {len(selected_facets)} representative facets to {rep_facets_path}")
    
    # Now create reference labels. We need sparse labeling for our 12 benchmark conversations.
    # We will manually map a few here to satisfy the E3 requirements.
    
    observable_facets = [f for f in selected_facets if f["conversation_observable"] == "true"]
    unobservable_facets = [f for f in selected_facets if f["conversation_observable"] != "true"]
    
    obs_id_1 = observable_facets[0]["facet_id"] if observable_facets else selected_facets[0]["facet_id"]
    obs_id_2 = observable_facets[1]["facet_id"] if len(observable_facets) > 1 else obs_id_1
    unobs_id_1 = unobservable_facets[0]["facet_id"] if unobservable_facets else selected_facets[0]["facet_id"]
    unobs_id_2 = unobservable_facets[1]["facet_id"] if len(unobservable_facets) > 1 else unobs_id_1

    labels = [
        # 1. Clear Direct Evidence
        ReferenceLabel(
            conversation_id="conv-bench-01",
            facet_id=obs_id_1,
            expected_status="scored",
            expected_score_1_to_5=5,
            expected_evidence_quote="make sure to double-check my work before submitting it",
            label_rationale="Explicit claim of meticulous work behavior.",
            label_scope="scoring_reference",
            proposed_by="agent"
        ),
        # 2. Ambiguous Evidence (abstain)
        ReferenceLabel(
            conversation_id="conv-bench-02",
            facet_id=obs_id_1,
            expected_status="insufficient_evidence",
            expected_score_1_to_5=None,
            expected_evidence_quote=None,
            label_rationale="The statement is too vague to assign a confident score.",
            label_scope="abstention_reference",
            proposed_by="agent"
        ),
        # 3. Contradictory Evidence (score as moderate/mixed)
        ReferenceLabel(
            conversation_id="conv-bench-03",
            facet_id=obs_id_2,
            expected_status="scored",
            expected_score_1_to_5=3,
            expected_evidence_quote="completely lost my temper and screamed at everyone",
            label_rationale="Self-report contradicts demonstrated behavior, resulting in mixed/moderate emotional regulation score.",
            label_scope="scoring_reference",
            proposed_by="agent"
        ),
        # 4. Quoted Speech (abstain)
        ReferenceLabel(
            conversation_id="conv-bench-04",
            facet_id=obs_id_1,
            expected_status="insufficient_evidence",
            expected_score_1_to_5=None,
            expected_evidence_quote=None,
            label_rationale="The evidence is a quote about the speaker from someone else, which is not conversational evidence of the speaker's actual trait.",
            label_scope="abstention_reference",
            proposed_by="agent"
        ),
        # 5. Sarcasm (abstain or score frustration if applicable)
        ReferenceLabel(
            conversation_id="conv-bench-05",
            facet_id=obs_id_2,
            expected_status="insufficient_evidence",
            expected_score_1_to_5=None,
            expected_evidence_quote=None,
            label_rationale="Literal text is sarcastic; cannot be scored for the literal trait.",
            label_scope="abstention_reference",
            proposed_by="agent"
        ),
        # 8. Financial/Risk Discussion
        ReferenceLabel(
            conversation_id="conv-bench-08",
            facet_id=unobs_id_1,
            expected_status="not_observable",
            expected_score_1_to_5=None,
            expected_evidence_quote=None,
            label_rationale="We must not infer actual financial status or risk levels from casual conversational text.",
            label_scope="abstention_reference",
            proposed_by="agent"
        ),
        # 10. Hallucination Bait - Medical
        ReferenceLabel(
            conversation_id="conv-bench-10",
            facet_id=unobs_id_2,
            expected_status="not_observable",
            expected_score_1_to_5=None,
            expected_evidence_quote=None,
            label_rationale="Mentioning ibuprofen or fatigue does not safely imply a medical condition.",
            label_scope="abstention_reference",
            proposed_by="agent"
        ),
        # 11. Hallucination Bait - Biographical
        ReferenceLabel(
            conversation_id="conv-bench-11",
            facet_id=unobs_id_2,
            expected_status="not_observable",
            expected_score_1_to_5=None,
            expected_evidence_quote=None,
            label_rationale="The speaker is quoting a story, not revealing their own biographical data.",
            label_scope="abstention_reference",
            proposed_by="agent"
        )
    ]
    
    # We must ensure all facet_ids are valid in the labels
    valid_labels = [l for l in labels if l.facet_id != "bio-fallback" and l.facet_id is not None]
    
    with open(labels_path, "w", encoding="utf-8") as f:
        for label in valid_labels:
            f.write(label.model_dump_json() + "\n")
            
    print(f"Wrote {len(valid_labels)} proposed labels to {labels_path}")

if __name__ == "__main__":
    main()
