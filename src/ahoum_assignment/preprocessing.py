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


def process_file(input_path: Path, output_path: Path) -> None:
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
    
    records = []
    for i, raw_line in enumerate(lines):
        # Skip header explicitly if it's literally the first line
        if i == 0 and raw_line.strip() == "Facets":
            continue
            
        norm = normalize_facet(raw_line)
        malf, reason = is_malformed(raw_line, norm)
        
        fid = generate_id(raw_line, i)
        
        record = {
            "facet_id": fid,
            "facet_raw": raw_line,  # Preserve raw text exactly
            "facet_normalized": norm,
            "is_malformed": "true" if malf else "false",
            "malformed_reason": reason,
            "facet_category": "TODO_PLACEHOLDER",
            "facet_type": "TODO_PLACEHOLDER",
            "conversation_observable": "false" if malf else "uncertain",
            "observability_reason": "Malformed" if malf else "Placeholder",
            "sensitivity": "",
            "scoring_definition": "",
            "anchor_1": "",
            "anchor_3": "",
            "anchor_5": "",
            "abstention_reason": reason if malf else "Not yet classified",
            "review_required": "true",
            "preprocessing_version": "v1.0"
        }
        records.append(record)
        
    with open(output_path, 'w', encoding='utf-8', newline='') as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
