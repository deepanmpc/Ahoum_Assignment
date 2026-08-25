import argparse
import json
import uuid
import sys
import datetime
from pathlib import Path

from ahoum_assignment.config import load_config
from ahoum_assignment.benchmark_models import BenchmarkConversation, ReferenceLabel
from ahoum_assignment.evaluation.models import EvaluationResult, LabelComparison
from ahoum_assignment.evaluation.metrics import (
    calculate_retrieval_metrics,
    calculate_scoring_metrics,
    calculate_abstention_metrics,
    calculate_reliability_metrics
)
from ahoum_assignment.evaluation.comparison import compare_label

from ahoum_assignment.semantic_retriever import retrieve_semantic_candidates
from ahoum_assignment.keyword_router import KeywordRouter
from ahoum_assignment.hybrid_retriever import merge_retrieval_results
from ahoum_assignment.embeddings import FakeDeterministicEmbedder, SentenceTransformerEmbedder
from ahoum_assignment.scoring_service import score_conversation
from ahoum_assignment.result_aggregator import aggregate_results, ConversationScoringResult
from ahoum_assignment.providers.factory import create_provider
from ahoum_assignment.providers.base import BaseProvider, ProviderResponse

class EvalMockProvider(BaseProvider):
    @property
    def provider_name(self) -> str: return "mock"
    @property
    def model_name(self) -> str: return "mock-eval"
    def generate(self, prompt: str) -> ProviderResponse:
        import re
        ids = re.findall(r"facet_id: (\S+)", prompt)
        results = [{
            "facet_id": fid,
            "status": "scored",
            "score_1_to_5": 3,
            "confidence_0_to_1": 0.9,
            "evidence_quote": "mock evidence",
            "reason": "mock reason"
        } for fid in ids]
        return ProviderResponse(
            text=json.dumps({"results": results}),
            provider_name=self.provider_name,
            model_name=self.model_name,
            latency_ms=10.0
        )

def get_git_hash() -> str:
    import subprocess
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

def load_jsonl(path: Path, model_cls):
    items = []
    if not path.exists(): return items
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            items.append(model_cls.model_validate_json(line))
    return items

def main():
    parser = argparse.ArgumentParser(description="Evaluate the facet scoring baseline")
    parser.add_argument("--config", type=Path, default=Path("config.toml"))
    parser.add_argument("--benchmark-path", type=Path, default=Path("data/examples/benchmark_conversations.jsonl"))
    parser.add_argument("--labels-path", type=Path, default=Path("data/examples/reference_labels.jsonl"))
    parser.add_argument("--retrieval-mode", choices=["semantic_only", "keyword_only", "hybrid"], default="hybrid")
    parser.add_argument("--provider", choices=["mock", "configured"], default="mock")
    parser.add_argument("--include-proposed", action="store_true")
    parser.add_argument("--run-name", type=str, default="")
    parser.add_argument("--output-dir", type=Path, default=Path("data/outputs"))
    parser.add_argument("--fail-on-validation-error", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    run_id = args.run_name or f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    out_dir = args.output_dir / run_id
    if out_dir.exists():
        print(f"Error: Run directory {out_dir} already exists.")
        sys.exit(1)
    out_dir.mkdir(parents=True, exist_ok=True)

    conversations = {c.conversation_id: c for c in load_jsonl(args.benchmark_path, BenchmarkConversation)}
    all_labels = load_jsonl(args.labels_path, ReferenceLabel)
    if args.include_proposed:
        labels = all_labels
        label_policy = "include_proposed"
    else:
        labels = [l for l in all_labels if l.reviewer_status in ["reviewed_accepted", "reviewed_changed"]]
        label_policy = "reviewed_only"

    if not labels:
        print("Warning: No labels found to evaluate against under the current policy.")

    root = Path(__file__).resolve().parents[1]
    cat_path = root / "data" / "processed" / "facet_catalogue.csv"
    rules_path = root / "config" / "routing_rules.toml"
    sem_idx_path = root / "data" / "processed" / "facet_embeddings.npz"
    sem_meta_path = root / "data" / "processed" / "facet_index_metadata.json"

    try:
        import sentence_transformers
        embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
    except ImportError:
        embedder = FakeDeterministicEmbedder(dim=384)

    kw_ret = KeywordRouter(rules_path, cat_path)
    provider = EvalMockProvider() if args.provider == "mock" else create_provider(config)

    retrieval_outputs = {}
    scoring_outputs = {}
    comparisons = []

    for conv_id, conv in conversations.items():
        if args.retrieval_mode == "semantic_only":
            ret = retrieve_semantic_candidates(conv.text, embedder, sem_idx_path, sem_meta_path, cat_path, top_k=25, conversation_id=conv_id)
        elif args.retrieval_mode == "keyword_only":
            ret = kw_ret.retrieve(conv.text, conversation_id=conv_id)
        else:
            sem_result = retrieve_semantic_candidates(conv.text, embedder, sem_idx_path, sem_meta_path, cat_path, top_k=50, conversation_id=conv_id)
            kw_result = kw_ret.retrieve(conv.text, conversation_id=conv_id)
            ret = merge_retrieval_results(sem_result, kw_result, top_k=25, semantic_weight=0.6, keyword_weight=0.4, hybrid_threshold=0.3)
        
        retrieval_outputs[conv_id] = ret
        
        scoring_res = score_conversation(
            conversation_id=conv_id,
            conversation_text=conv.text,
            retrieval_result=ret,
            provider=provider,
            catalogue_path=cat_path,
            batch_size=config.scoring_batch_size,
            dry_run=False
        )
        agg_res = aggregate_results(ret, scoring_res)
        scoring_outputs[conv_id] = agg_res
        
        conv_labels = [l for l in labels if l.conversation_id == conv_id]
        for lbl in conv_labels:
            is_bait = "hallucination_bait" in conv.scenario_type
            comp = compare_label(lbl, agg_res, is_bait=is_bait)
            comparisons.append(comp)

    ret_metrics = calculate_retrieval_metrics(labels, retrieval_outputs, conversations)
    score_metrics = calculate_scoring_metrics(comparisons)
    abst_metrics = calculate_abstention_metrics(comparisons)
    rel_metrics = calculate_reliability_metrics(scoring_outputs)

    config_snap = {
        "model_provider": config.model_provider,
        "model_name": config.model_name,
        "batch_size": config.scoring_batch_size
    }
    
    eval_res = EvaluationResult(
        run_id=run_id,
        timestamp=datetime.datetime.now().isoformat(),
        commit_hash=get_git_hash(),
        config_snapshot=config_snap,
        retrieval_mode=args.retrieval_mode,
        provider=args.provider,
        label_policy=label_policy,
        benchmark_version="1.0",
        total_conversations=len(conversations),
        total_labels_evaluated=len(labels),
        retrieval=ret_metrics,
        scoring=score_metrics,
        abstention=abst_metrics,
        reliability=rel_metrics
    )

    with open(out_dir / "evaluation_summary.json", "w") as f:
        f.write(eval_res.model_dump_json(indent=2))

    with open(out_dir / "run_metadata.json", "w") as f:
        json.dump({
            "run_id": run_id,
            "timestamp": eval_res.timestamp,
            "commit_hash": eval_res.commit_hash,
            "config": config_snap,
            "retrieval_mode": args.retrieval_mode,
            "provider": args.provider,
            "label_policy": label_policy
        }, f, indent=2)

    with open(out_dir / "retrieval_outputs.jsonl", "w") as f:
        for r in retrieval_outputs.values():
            f.write(r.model_dump_json() + "\n")

    import dataclasses
    with open(out_dir / "scoring_outputs.jsonl", "w") as f:
        for r in scoring_outputs.values():
            if hasattr(r, "model_dump_json"):
                f.write(r.model_dump_json() + "\n")
            else:
                f.write(json.dumps(dataclasses.asdict(r), default=str) + "\n")

    with open(out_dir / "per_label_comparisons.jsonl", "w") as f:
        for c in comparisons:
            f.write(c.model_dump_json() + "\n")

    print(f"\nEvaluation complete! Artifacts saved to {out_dir}")
    print(f"Evaluated {len(conversations)} conversations and {len(labels)} labels.")
    print(f"Retrieval Recall@5: {ret_metrics.recall_at_5}")
    print(f"Scoring Exact Match Rate: {score_metrics.exact_agreement_rate}")
    print(f"Abstention Unsupported Rate: {abst_metrics.unsupported_score_rate}")

if __name__ == "__main__":
    main()
