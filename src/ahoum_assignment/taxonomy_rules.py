import re
import csv
from pathlib import Path


# Core taxonomy dictionaries for validation
CATEGORIES = {
    "communication", "emotional_regulation", "decision_making", "social_interaction",
    "work_habits", "values", "skills", "lifestyle", "health_medical", 
    "biography_external", "religion_culture", "finance_risk", "unclear"
}

TYPES = {
    "conversational_trait", "conversational_behavior", "skill_or_knowledge",
    "preference_or_habit", "medical_or_diagnostic", "external_biographical_fact",
    "religious_or_cultural_practice", "unclear_or_malformed"
}

# The rules map a regex pattern to:
# (category, type, observable, sensitivity, reason)
RULES = [
    # Medical / Health (High Risk)
    (r'\b(blood pressure|fsh|hba1c|wbc|cholesterol|level|count|diagnosis|disease|medical|pain|anatomy|symptom|clinical)\b', 
     "health_medical", "medical_or_diagnostic", "false", "high_risk", "Clinical biomarker or medical diagnosis requires objective medical evidence"),
     
    # Religious / Cultural (Sensitive)
    (r'\b(sufi|quran|bahá’í|spiritual|religion|pilgrimage|church|prayer|ritual)\b',
     "religion_culture", "religious_or_cultural_practice", "false", "sensitive", "Religious or cultural practice requires external or self-reported history observation"),
     
    # Biography / External Facts
    (r'\b(trips|participation|length|attendance|history|salary|income|demographic|age|cycles|retreat)\b',
     "biography_external", "external_biographical_fact", "false", "ordinary", "Requires external historical or biographical confirmation"),
     
    # Skills and Task Execution
    (r'\b(arithmetic|reasoning|knowledge|math|coding|speed|specialist)\b',
     "skills", "skill_or_knowledge", "false", "ordinary", "Skill evaluation requires task execution evidence, not casual self-description"),
     
    # Communication
    (r'\b(talkative|assertion|assertiveness|listening|articulate|hesitation)\b',
     "communication", "conversational_behavior", "true", "ordinary", ""),
     
    # Emotions
    (r'\b(anxiety|anger|moroseness|desperation|emotionalism|merriness|discontentment|negative affect|acidity|sensitiveness)\b',
     "emotional_regulation", "conversational_trait", "true", "ordinary", ""),
     
    # Risk / Finance
    (r'\b(risk|betting|gambling|finance|risktaking)\b',
     "finance_risk", "preference_or_habit", "uncertain", "sensitive", "Risk preference requires contextual validation to be observable"),

    # Social Interaction / Relationships
    (r'\b(aloofness|relationship|submissiveness|overprotectiveness|affiliation|passive-aggressive|disrespect)\b',
     "social_interaction", "conversational_behavior", "true", "ordinary", ""),

    # Values / Work Habits / Habits
    (r'\b(patience|honesty|humility|leadership|chivalrousness|genuine|determinedness|common-sense)\b',
     "values", "conversational_trait", "true", "ordinary", "")
]

def load_overrides(filepath: Path) -> dict:
    """Load manual overrides from a CSV file."""
    overrides = {}
    if filepath.is_file():
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'facet_normalized' in row:
                    overrides[row['facet_normalized']] = row
    return overrides


def classify_facet(norm_str: str, is_malf: bool, overrides: dict) -> dict:
    if is_malf:
        return {
            "facet_category": "unclear",
            "facet_type": "unclear_or_malformed",
            "conversation_observable": "false",
            "observability_reason": "Malformed facet cannot be evaluated",
            "sensitivity": "ordinary",
            "abstention_reason": "Malformed data",
            "review_required": "true"
        }
        
    if norm_str in overrides:
        o = overrides[norm_str]
        return {
            "facet_category": o.get("facet_category", "unclear"),
            "facet_type": o.get("facet_type", "unclear_or_malformed"),
            "conversation_observable": o.get("conversation_observable", "uncertain"),
            "observability_reason": o.get("observability_reason", "Manual override applied"),
            "sensitivity": o.get("sensitivity", "ordinary"),
            "abstention_reason": o.get("abstention_reason", "Manual override applied"),
            "review_required": o.get("review_required", "false").lower() == "true"
        }
        
    # Default state if no rules match
    result = {
        "facet_category": "unclear",
        "facet_type": "unclear_or_malformed",
        "conversation_observable": "uncertain",
        "observability_reason": "No explicit rule matched",
        "sensitivity": "ordinary",
        "abstention_reason": "Classification uncertain; requires human review",
        "review_required": "true"
    }
    
    for pattern, cat, ftype, obs, sens, reason in RULES:
        if re.search(pattern, norm_str):
            result.update({
                "facet_category": cat,
                "facet_type": ftype,
                "conversation_observable": obs,
                "observability_reason": reason if obs != "true" else "Direct linguistic evidence possible in short conversation",
                "sensitivity": sens,
                "abstention_reason": reason if obs != "true" else "",
            })
            
            # Review required for uncertain/false observability or sensitive/high-risk
            if obs in ("uncertain", "false") or sens in ("sensitive", "high_risk"):
                result["review_required"] = "true"
            else:
                result["review_required"] = "false"
            
            break
            
    return result
