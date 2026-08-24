import csv
import re
import tomllib
import uuid
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Tuple

from ahoum_assignment.models import (
    RetrievalCandidate, 
    RetrievalResult, 
    RetrievalDiagnostics
)

def build_regex(phrases: List[str]) -> re.Pattern | None:
    if not phrases:
        return None
    # Use word boundaries to avoid naive substring errors (e.g., 'asset' in 'cassette')
    escaped = [re.escape(p.strip().lower()) for p in phrases if p.strip()]
    if not escaped:
        return None
    pattern = r'\b(?:' + '|'.join(escaped) + r')\b'
    return re.compile(pattern, re.IGNORECASE)

class KeywordRouter:
    def __init__(self, rules_path: Path, catalogue_path: Path):
        self.rules_path = rules_path
        self.catalogue_path = catalogue_path
        self.rules = self._load_rules()
        self.catalogue = self._load_catalogue()
        self.category_patterns = self._compile_patterns()
        
    def _load_rules(self) -> Dict[str, Any]:
        with open(self.rules_path, 'rb') as f:
            return tomllib.load(f)
            
    def _load_catalogue(self) -> List[Dict[str, str]]:
        if not self.catalogue_path.exists():
            raise FileNotFoundError(f"Catalogue not found at {self.catalogue_path}")
        cat = []
        with open(self.catalogue_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cat.append(row)
        return cat

    def _compile_patterns(self) -> Dict[str, dict]:
        compiled = {}
        for cat, data in self.rules.get("categories", {}).items():
            keywords = data.get("keywords", [])
            # Add multilingual support if present
            ml = data.get("multilingual", {})
            if "keywords" in ml:
                keywords.extend(ml["keywords"])
                
            neg_keywords = data.get("negative_keywords", [])
            
            compiled[cat] = {
                "weight": data.get("weight", 0.5),
                "priority": data.get("priority", 99),
                "pos_re": build_regex(keywords),
                "neg_re": build_regex(neg_keywords)
            }
        return compiled

    def match_text(self, text: str) -> Dict[str, Tuple[float, List[str]]]:
        """Returns a dict mapping matched categories to (score, list_of_matched_keywords)."""
        matches = {}
        config = self.rules.get("config", {})
        base_score = config.get("base_keyword_score", 0.5)
        score_per_match = config.get("score_per_match", 0.1)
        
        for cat, pat in self.category_patterns.items():
            pos_re = pat["pos_re"]
            neg_re = pat["neg_re"]
            
            if not pos_re:
                continue
                
            # Check negative constraints first
            if neg_re and neg_re.search(text):
                continue
                
            found = pos_re.findall(text)
            if found:
                # Normalize matched keywords to lowercase
                found = list(set([f.lower() for f in found]))
                raw_score = base_score + (len(found) * score_per_match)
                # Cap score by category weight
                final_score = min(raw_score, pat["weight"])
                matches[cat] = (final_score, found)
                
        return matches

    def retrieve(self, text: str, conversation_id: str = None) -> RetrievalResult:
        cat_matches = self.match_text(text)
        
        candidates = []
        warnings = []
        
        if not cat_matches:
            warnings.append("No keyword rules matched the conversation text.")
            
        config = self.rules.get("config", {})
        max_per_cat = config.get("max_candidates_per_category", 5)
        
        # Group eligible catalogue facets by category
        eligible_by_cat = defaultdict(list)
        for row in self.catalogue:
            cat = row.get("facet_category", "")
            # STRICT REQUIREMENT: Never include non-observable/malformed facets
            if row.get("conversation_observable") != "true":
                continue
            eligible_by_cat[cat].append(row)
            
        # Build candidates
        total_matched_facets = 0
        excluded_non_observable = 0
        
        candidates_data = []
        for cat, (score, matched_kws) in cat_matches.items():
            available = eligible_by_cat.get(cat, [])
            
            # Sort deterministically by facet_id
            available.sort(key=lambda x: x["facet_id"])
            
            # Count excluded non-observable traits theoretically in this category
            # (Just for diagnostic correctness, we'll estimate based on total catalogue)
            cat_total = sum(1 for r in self.catalogue if r.get("facet_category") == cat)
            excluded_non_observable += (cat_total - len(available))
            
            # Limit per category
            selected = available[:max_per_cat]
            total_matched_facets += len(selected)
            
            for row in selected:
                candidates_data.append({
                    "facet_id": row["facet_id"],
                    "facet_raw": row["facet_raw"],
                    "facet_normalized": row["facet_normalized"],
                    "facet_category": row["facet_category"],
                    "conversation_observable": "true",
                    "keyword_score": score,
                    "hybrid_score": score, # Hybrid is just keyword for now
                    "matched_keywords": matched_kws,
                    "matched_categories": [cat],
                    "inclusion_reason": f"Rule match for category '{cat}' via keywords: {', '.join(matched_kws)}"
                })
                
        # Global sort across all categories (highest score first, tie-break by facet_id)
        candidates_data.sort(key=lambda c: (-c["keyword_score"], c["facet_id"]))
        
        # Instantiate RetrievalCandidate with correct ranks
        candidates = []
        for i, c_data in enumerate(candidates_data, start=1):
            c_data["rank"] = i
            candidates.append(RetrievalCandidate(**c_data))
            
        diag = RetrievalDiagnostics(
            keyword_candidate_count=len(candidates),
            merged_candidate_count=len(candidates),
            excluded_non_observable_count=excluded_non_observable,
            fallback_behavior="none" if candidates else "empty_list"
        )
        
        return RetrievalResult(
            conversation_id=conversation_id or str(uuid.uuid4()),
            candidate_count=len(candidates),
            candidates=candidates,
            excluded_count=excluded_non_observable,
            retrieval_config_metadata={"router": "keyword", "max_per_cat": max_per_cat},
            index_version="keyword_rules_v1",
            warnings=warnings,
            diagnostics=diag
        )
