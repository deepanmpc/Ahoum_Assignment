# Reference Label Review Workflow

The benchmark labels are initially created by coding agents as `proposed` labels. To maintain evaluation integrity, the project owner must review and explicitly approve or change these labels before they are used as a ground-truth reference.

## Review Tool

We provide a lightweight interactive CLI to review the labels.

```bash
python scripts/review_labels.py
```

### Review Process
1. The tool loads `data/examples/benchmark_conversations.jsonl` and `data/examples/reference_labels.jsonl`.
2. It loops through all labels with the status `proposed`.
3. For each label, it prints the conversation text, the selected facet, the proposed status, score (if any), evidence quote, and the rationale.
4. You are prompted to provide an action:
   - `[a]ccept`: Marks the label as `reviewed_accepted`.
   - `[r]eject`: Marks the label as `rejected`.
   - `[e]dit`: Allows you to provide a new status, score, and quote, marking it as `reviewed_changed`.
   - `[s]kip`: Leaves the label as `proposed` and moves to the next.
   - `[q]uit`: Exits the tool and saves progress.

### Output
The reviewed labels are saved to `data/examples/reference_labels_reviewed.jsonl`. 

> **Important**: This output file is generated separately to preserve the original proposals.

## Traceability Guarantees
- The original labels in `reference_labels.jsonl` are never mutated.
- The `reviewer_name_or_alias` and `review_date` are recorded.
- Pydantic schema rules strictly enforce that if you edit a label to be `scored`, you **must** provide a 1-5 score and an exact evidence quote, and if you edit it to an abstention, the score must be null.
