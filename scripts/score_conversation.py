"""Score a conversation against retrieved facets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ahoum_assignment.config import load_config
from ahoum_assignment.semantic_retriever import retrieve_semantic_candidates
from ahoum_assignment.keyword_router import KeywordRouter
from ahoum_assignment.hybrid_retriever import merge_retrieval_results
from ahoum_assignment.scoring_service import score_conversation
from ahoum_assignment.result_aggregator import aggregate_results
from ahoum_assignment.result_renderer import render
from ahoum_assignment.embeddings import FakeDeterministicEmbedder, SentenceTransformerEmbedder
from ahoum_assignment.providers.factory import create_provider
from ahoum_assignment.providers.base import ProviderError


def main():
    parser = argparse.ArgumentParser(description="Score conversation facets")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Conversation text")
    group.add_argument("--file", type=str, help="Conversation text file")

    parser.add_argument("--conversation-id", default="conv-1")
    parser.add_argument("--config", default="config.toml")
    parser.add_argument("--dry-run", action="store_true",
                        help="Build batches/prompts without calling a provider")
    parser.add_argument("--output", type=str, help="JSON output path")
    parser.add_argument("--human", action="store_true",
                        help="Print human-readable summary")

    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        text = args.text

    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / args.config)

    # Retrieval
    try:
        import sentence_transformers  # noqa: F401
        embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
    except ImportError:
        embedder = FakeDeterministicEmbedder(dim=384)

    npz = root / "data" / "processed" / "facet_embeddings.npz"
    meta = root / "data" / "processed" / "facet_index_metadata.json"

    sem = retrieve_semantic_candidates(
        text, embedder, npz, meta, cfg.facet_catalogue_csv,
        top_k=50, threshold=0.1,
    )
    kw = KeywordRouter(
        root / "config" / "routing_rules.toml", cfg.facet_catalogue_csv
    ).retrieve(text)

    hybrid = merge_retrieval_results(
        sem, kw,
        semantic_weight=cfg.retrieval_semantic_weight,
        keyword_weight=cfg.retrieval_keyword_weight,
        top_k=cfg.retrieval_top_k,
    )

    # Provider
    provider = None
    if not args.dry_run:
        try:
            provider = create_provider(cfg)
        except ProviderError as exc:
            print(f"Provider setup failed: {exc.safe_message}")
            print("Use --dry-run to build prompts without a provider.")
            sys.exit(1)

    scoring = score_conversation(
        conversation_id=args.conversation_id,
        conversation_text=text,
        retrieval_result=hybrid,
        provider=provider,
        catalogue_path=cfg.facet_catalogue_csv,
        batch_size=cfg.scoring_batch_size,
        dry_run=args.dry_run,
    )

    agg = aggregate_results(hybrid, scoring)

    if args.human:
        print(render(agg))
    elif args.output:
        Path(args.output).write_text(
            json.dumps(agg.to_dict(), indent=2), encoding="utf-8"
        )
        print(f"Written to {args.output}")
    else:
        print(json.dumps(agg.to_dict(), indent=2))


if __name__ == "__main__":
    main()
