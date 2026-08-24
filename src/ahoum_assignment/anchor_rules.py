import csv
from pathlib import Path


def load_anchor_overrides(filepath: Path) -> dict:
    """Load manual scoring definitions and anchors from a CSV file."""
    overrides = {}
    if filepath.is_file():
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'facet_normalized' in row:
                    overrides[row['facet_normalized']] = row
    return overrides


def apply_anchors(record: dict, overrides: dict) -> dict:
    """Apply scoring definitions and anchors based on observability."""
    norm = record["facet_normalized"]
    
    # Non-observable facets MUST NOT have anchors
    if record.get("conversation_observable") != "true":
        record["scoring_definition"] = ""
        record["anchor_1"] = ""
        record["anchor_3"] = ""
        record["anchor_5"] = ""
        return record
        
    # Apply manual overrides if present
    if norm in overrides:
        o = overrides[norm]
        record["scoring_definition"] = o.get("scoring_definition", "")
        record["anchor_1"] = o.get("anchor_1", "")
        record["anchor_3"] = o.get("anchor_3", "")
        record["anchor_5"] = o.get("anchor_5", "")
        return record
        
    # Apply deterministic templates based on classification
    ftype = record.get("facet_type", "")
    
    if ftype == "conversational_behavior":
        record["scoring_definition"] = f"Measures the frequency and intensity of {norm} behavior in conversation."
        record["anchor_1"] = f"Strong linguistic evidence of the low end (e.g., deliberate avoidance of {norm})."
    else:
        record["scoring_definition"] = f"Measures the conversational expression of the trait: {norm}."
        record["anchor_1"] = f"Strong linguistic evidence of the low end (e.g., explicitly demonstrating the opposite of {norm})."

    record["anchor_3"] = f"Mixed, moderate, or limited but sufficient evidence of {norm}."
    record["anchor_5"] = f"Strong and repeated linguistic evidence of the high end of {norm}."
        
    return record
