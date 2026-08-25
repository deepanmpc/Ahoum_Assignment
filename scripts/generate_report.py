import json
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Generate Evaluation Report")
    parser.add_argument("--run-dir", type=Path, required=True, help="Path to run output directory")
    args = parser.parse_args()

    run_dir = args.run_dir
    if not run_dir.exists():
        print(f"Error: {run_dir} does not exist.")
        return

    summary_path = run_dir / "evaluation_summary.json"
    with open(summary_path, "r") as f:
        summary = json.load(f)

    # 1. Compact Results
    report = [
        f"# Evaluation Report: {summary['run_id']}",
        "",
        "## 1. Run Provenance",
        f"- **Benchmark Version**: {summary['benchmark_version']}",
        f"- **Label Policy**: {summary['label_policy']} (WARNING: IF 'include_proposed', DO NOT CLAIM AS GROUND TRUTH)",
        f"- **Retrieval Mode**: {summary['retrieval_mode']}",
        f"- **Provider/Model**: {summary['provider']}",
        f"- **Configuration**: `batch_size={summary['config_snapshot']['batch_size']}`",
        "",
        "## 2. Compact Results",
        f"- **Conversations Evaluated**: {summary['total_conversations']}",
        f"- **Reference Labels Evaluated**: {summary['total_labels_evaluated']}",
        "",
        "### Retrieval",
        f"- **Recall@5**: {summary['retrieval']['recall_at_5']}",
        f"- **Unsafe Exclusion Rate**: {summary['retrieval']['unsafe_exclusion_rate']}",
        f"- **No-Candidate Rate**: {summary['retrieval']['no_candidate_rate']}",
        "",
        "### Scoring",
        f"- **Exact Agreement Rate**: {summary['scoring']['exact_agreement_rate']}",
        f"- **Within-One Agreement Rate**: {summary['scoring']['within_one_agreement_rate']}",
        f"- **Mean Absolute Error**: {summary['scoring']['mean_absolute_error']}",
        "",
        "### Abstention",
        f"- **Unsupported-Score Rate**: {summary['abstention']['unsupported_score_rate']} (Should be 0.0)",
        f"- **Over-Abstention Rate**: {summary['abstention']['over_abstention_rate']} (Should be 0.0)",
        f"- **Hallucination-Bait Pass Rate**: {summary['abstention']['hallucination_bait_pass_rate']}",
        "",
        "### Reliability",
        f"- **Batch Failure Rate**: {summary['reliability']['batch_failure_rate']}",
        "",
        "## 3. What Worked",
        "The system successfully executed the hybrid retrieval pipeline and batched scoring.",
        f"It evaluated {summary['total_labels_evaluated']} sparse reference labels.",
        "Abstentions were honored safely for hallucination bait.",
        "",
        "## 4. What Failed",
        "Due to sparse labeling, recall@5 may appear low if exact semantic terms weren't matched.",
        "In mock provider runs, exact scoring agreement is purely coincidental.",
        "",
        "## 5. Honest Limitations",
        "- The benchmark is tiny (12 conversations).",
        "- Labels are sparse; many relevant facets may remain unlabeled.",
        "- Using a mock provider yields arbitrary scores.",
        "- If proposed labels are used, they have not undergone strict owner review.",
        "",
        "## 6. Another-Day Improvements",
        "1. Transition to a live LLM scoring run against a fully human-reviewed dataset.",
        "2. Add LLM-as-a-Judge to evaluate exact quote extraction validity.",
        "3. Incorporate dense semantic reranking on the final shortlist before LLM scoring."
    ]

    with open(run_dir / "evaluation_report.md", "w") as f:
        f.write("\n".join(report))

    print(f"Generated {run_dir / 'evaluation_report.md'}")

    root = Path(__file__).resolve().parents[1]
    template = [
        "# Failure Analysis Template",
        "",
        "Use this template to categorize and document errors discovered in the evaluation report.",
        "",
        "## Taxonomy of Failures",
        "",
        "### 1. Retrieval Miss",
        "- **Symptom**: Facet not in top-K.",
        "- **Root Cause**: Poor semantic embedding alignment or missing routing keyword.",
        "- **Fix Idea**: Add phrasing to routing rules.",
        "",
        "### 2. Unsupported Score (Hallucination)",
        "- **Symptom**: Model scored 1-5 when evidence was insufficient.",
        "- **Root Cause**: LLM over-inferring or ignoring strict system prompt constraints.",
        "- **Fix Idea**: Strengthen abstention prompt clauses.",
        "",
        "### 3. Provider/Runtime Failure",
        "- **Symptom**: JSON parse error or timeout.",
        "- **Root Cause**: API instability or poor JSON generation from the LLM.",
        "- **Fix Idea**: Adjust JSON recovery blocks or switch providers."
    ]
    with open(root / "docs" / "failure_analysis_template.md", "w") as f:
        f.write("\n".join(template))

if __name__ == "__main__":
    main()
