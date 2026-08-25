import json
from pathlib import Path
from datetime import datetime
import sys

from ahoum_assignment.benchmark_models import BenchmarkConversation, ReferenceLabel

def load_conversations(path: Path) -> dict:
    if not path.exists():
        return {}
    convs = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            c = BenchmarkConversation.model_validate_json(line)
            convs[c.conversation_id] = c
    return convs

def load_labels(path: Path) -> list:
    if not path.exists():
        return []
    labels = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            labels.append(ReferenceLabel.model_validate_json(line))
    return labels

def save_labels(path: Path, labels: list):
    with open(path, "w", encoding="utf-8") as f:
        for label in labels:
            f.write(label.model_dump_json() + "\n")

def main():
    root = Path(__file__).resolve().parents[1]
    conv_path = root / "data" / "examples" / "benchmark_conversations.jsonl"
    labels_path = root / "data" / "examples" / "reference_labels.jsonl"
    reviewed_path = root / "data" / "examples" / "reference_labels_reviewed.jsonl"

    conversations = load_conversations(conv_path)
    # Load previously reviewed ones if any, else start from proposed
    if reviewed_path.exists():
        labels = load_labels(reviewed_path)
    else:
        labels = load_labels(labels_path)

    if not labels:
        print("No labels found to review.")
        return

    reviewer = input("Enter your reviewer alias: ").strip() or "anonymous"

    pending = [l for l in labels if l.reviewer_status == "proposed"]
    print(f"Found {len(pending)} proposed labels to review.")

    for i, label in enumerate(labels):
        if label.reviewer_status != "proposed":
            continue

        conv = conversations.get(label.conversation_id)
        if not conv:
            print(f"Conversation {label.conversation_id} not found! Skipping.")
            continue

        print("\n" + "="*60)
        print(f"Label {i+1}/{len(labels)}")
        print(f"Conversation [{conv.conversation_id}]: {conv.text}")
        print(f"Facet ID: {label.facet_id}")
        print(f"Proposed Status: {label.expected_status}")
        if label.expected_status == "scored":
            print(f"Proposed Score: {label.expected_score_1_to_5}")
            print(f"Evidence Quote: '{label.expected_evidence_quote}'")
        print(f"Rationale: {label.label_rationale}")
        print("="*60)

        while True:
            choice = input("Action: [a]ccept, [r]eject, [e]dit, [s]kip, [q]uit: ").strip().lower()
            if choice in ['a', 'r', 'e', 's', 'q']:
                break
            print("Invalid choice.")

        if choice == 'q':
            break
        elif choice == 's':
            continue
        elif choice == 'a':
            label.reviewer_status = "reviewed_accepted"
            label.reviewer_name_or_alias = reviewer
            label.review_date = datetime.now().isoformat()
            print("Label accepted.")
        elif choice == 'r':
            label.reviewer_status = "rejected"
            label.reviewer_name_or_alias = reviewer
            label.review_date = datetime.now().isoformat()
            print("Label rejected.")
        elif choice == 'e':
            new_status = input("New status (scored, insufficient_evidence, not_observable, retrieval_excluded): ").strip()
            if new_status in ["scored", "insufficient_evidence", "not_observable", "retrieval_excluded"]:
                label.expected_status = new_status
                if new_status == "scored":
                    score = input("New score (1-5): ").strip()
                    label.expected_score_1_to_5 = int(score) if score.isdigit() else None
                    quote = input("New evidence quote: ").strip()
                    label.expected_evidence_quote = quote
                else:
                    label.expected_score_1_to_5 = None
                    label.expected_evidence_quote = None
                
                label.reviewer_status = "reviewed_changed"
                label.reviewer_name_or_alias = reviewer
                label.review_date = datetime.now().isoformat()
                print("Label edited and saved.")
            else:
                print("Invalid status. Edit aborted.")

    save_labels(reviewed_path, labels)
    print(f"\nReview progress saved to {reviewed_path.relative_to(root)}.")

if __name__ == "__main__":
    main()
