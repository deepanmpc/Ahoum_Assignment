import re
import hashlib
import csv
from pathlib import Path


def normalize_facet(raw_str: str) -> str:
    s = raw_str
    # Remove obvious list-number prefixes like "899. " or "1) "
    s = re.sub(r'^\s*\d+[\.\)]\s+', '', s)
    # Normalize case consistently
    s = s.lower()
    # Remove accidental trailing colon punctuation
    s = re.sub(r':\s*$', '', s)
    # Collapse repeated internal whitespace and trim leading/trailing
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def is_malformed(raw_str: str, norm_str: str) -> tuple[bool, str]:
    if not raw_str.strip():
        return True, "Blank value"
    
    lower_raw = raw_str.strip().lower()
    if lower_raw in ("facets", "facet", "column1", "id", "category"):
        return True, "Header or import artifact"
        
    if not norm_str:
        return True, "Empty after normalization"
    
    # Entries consisting mostly of punctuation/numbers
    alnum_count = sum(c.isalnum() for c in norm_str)
    if len(norm_str) > 0 and (alnum_count / len(norm_str)) < 0.5:
        return True, "Consists mostly of punctuation or numbers"
    
    return False, ""


def generate_id(raw_str: str, index: int) -> str:
    # Stable deterministic ID
    hash_input = f"{index}:{raw_str}".encode('utf-8')
    return hashlib.md5(hash_input).hexdigest()[:12]


from ahoum_assignment.taxonomy_rules import classify_facet, load_overrides
from collections import Counter
import json

def process_file(input_path: Path, output_path: Path) -> dict:
    with open(input_path, 'r', encoding='utf-8-sig') as fin:
        lines = [line.strip("\n") for line in fin.readlines()]
    
    fieldnames = [
        "facet_id", "facet_raw", "facet_normalized", "is_malformed", 
        "malformed_reason", "facet_category", "facet_type", 
        "conversation_observable", "observability_reason", "sensitivity", 
        "scoring_definition", "anchor_1", "anchor_3", "anchor_5", 
        "abstention_reason", "review_required", "preprocessing_version"
    ]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    overrides_file = input_path.parent / "facet_overrides.csv"
    overrides = load_overrides(overrides_file)
    
    records = []
    
    # Audit tracking
    stats = {
        "categories": Counter(),
        "types": Counter(),
        "observability": Counter(),
        "sensitivity": Counter(),
        "review_required": Counter(),
        "examples": {
            "medical_or_diagnostic": [],
            "external_biographical_fact": [],
            "religious_or_cultural_practice": [],
            "conversational_trait": [],
            "unclear": [],
            "sensitive_or_high_risk": []
        }
    }
    
    for i, raw_line in enumerate(lines):
        if i == 0 and raw_line.strip() == "Facets":
            continue
            
        norm = normalize_facet(raw_line)
        malf, reason = is_malformed(raw_line, norm)
        
        fid = generate_id(raw_line, i)
        classification = classify_facet(norm, malf, overrides)
        
        record = {
            "facet_id": fid,
            "facet_raw": raw_line,
            "facet_normalized": norm,
            "is_malformed": "true" if malf else "false",
            "malformed_reason": reason,
            "facet_category": classification["facet_category"],
            "facet_type": classification["facet_type"],
            "conversation_observable": classification["conversation_observable"],
            "observability_reason": classification["observability_reason"],
            "sensitivity": classification["sensitivity"],
            "scoring_definition": "",
            "anchor_1": "",
            "anchor_3": "",
            "anchor_5": "",
            "abstention_reason": classification["abstention_reason"],
            "review_required": classification["review_required"],
            "preprocessing_version": "v1.1"
        }
        records.append(record)
        
        # Track stats
        stats["categories"][record["facet_category"]] += 1
        stats["types"][record["facet_type"]] += 1
        stats["observability"][record["conversation_observable"]] += 1
        stats["sensitivity"][record["sensitivity"]] += 1
        stats["review_required"][record["review_required"]] += 1
        
        # Collect examples
        t = record["facet_type"]
        s = record["sensitivity"]
        if t in stats["examples"] and len(stats["examples"][t]) < 5:
            stats["examples"][t].append(norm)
        if record["facet_category"] == "unclear" and len(stats["examples"]["unclear"]) < 5:
            stats["examples"]["unclear"].append(norm)
        if s in ("sensitive", "high_risk") and len(stats["examples"]["sensitive_or_high_risk"]) < 5:
            stats["examples"]["sensitive_or_high_risk"].append(norm)
        
    with open(output_path, 'w', encoding='utf-8', newline='') as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
        
    return stats
