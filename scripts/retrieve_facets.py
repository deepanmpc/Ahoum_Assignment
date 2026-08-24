import argparse
import json
import sys
from pathlib import Path

# Ensure local src/ can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ahoum_assignment.semantic_retriever import retrieve_semantic_candidates
from ahoum_assignment.keyword_router import KeywordRouter
from ahoum_assignment.hybrid_retriever import merge_retrieval_results
from ahoum_assignment.embeddings import FakeDeterministicEmbedder, SentenceTransformerEmbedder

def main():
    parser = argparse.ArgumentParser(description="Hybrid Facet Retrieval CLI")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Direct conversation text input")
    group.add_argument("--file", type=str, help="Text file input path")
    
    parser.add_argument("--top-k", type=int, default=20, help="Final candidates limit (default: 20)")
    parser.add_argument("--hybrid-threshold", type=float, default=0.3, help="Minimum hybrid score threshold")
    parser.add_argument("--semantic-weight", type=float, default=0.6, help="Weight for semantic similarity")
    parser.add_argument("--keyword-weight", type=float, default=0.4, help="Weight for explicit keyword hits")
    parser.add_argument("--output", type=str, help="Optional JSON output path")
    parser.add_argument("--human", action="store_true", help="Output human-readable explanation to stdout")
    
    args = parser.parse_args()
    
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: Could not read file at {args.file}")
            sys.exit(1)
    else:
        text = args.text
        
    root = Path(__file__).resolve().parents[1]
    catalogue_csv = root / "data" / "processed" / "facet_catalogue.csv"
    rules_toml = root / "config" / "routing_rules.toml"
    npz_path = root / "data" / "processed" / "facet_embeddings.npz"
    meta_path = root / "data" / "processed" / "facet_index_metadata.json"
    
    try:
        import sentence_transformers
        embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
    except ImportError:
        embedder = FakeDeterministicEmbedder(dim=384)
        
    try:
        router = KeywordRouter(rules_toml, catalogue_csv)
        
        kw_result = router.retrieve(text)
        
        sem_result = retrieve_semantic_candidates(
            text=text,
            embedder=embedder,
            npz_path=npz_path,
            meta_path=meta_path,
            catalogue_path=catalogue_csv,
            top_k=50, # Retrieve a wider semantic net to merge
            threshold=0.1
        )
        
        hybrid_result = merge_retrieval_results(
            semantic_result=sem_result,
            keyword_result=kw_result,
            semantic_weight=args.semantic_weight,
            keyword_weight=args.keyword_weight,
            hybrid_threshold=args.hybrid_threshold,
            top_k=args.top_k
        )
        
    except Exception as e:
        print(f"Hybrid Retrieval Error: {e}")
        sys.exit(1)
        
    out_data = hybrid_result.model_dump()
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(out_data, f, indent=2)
            
    if args.human:
        print(f"\n--- HYBRID RETRIEVAL SHORTLIST (Top {hybrid_result.candidate_count}) ---")
        if not hybrid_result.candidates:
            print("No candidates met the threshold requirements.")
        for c in hybrid_result.candidates:
            print(f"\n[{c.rank}] {c.facet_normalized} (ID: {c.facet_id})")
            print(f"    Category: {c.facet_category}")
            print(f"    Hybrid Score: {c.hybrid_score:.3f} | Semantic: {c.semantic_score or 0.0:.3f} | Keyword: {c.keyword_score or 0.0:.3f}")
            print(f"    Reason: {c.inclusion_reason}")
            if c.matched_keywords:
                print(f"    Matched terms: {', '.join(c.matched_keywords)}")
        
        print(f"\n--- DIAGNOSTICS ---")
        print(f"Semantic Candidates  : {hybrid_result.diagnostics.semantic_candidate_count}")
        print(f"Keyword Candidates   : {hybrid_result.diagnostics.keyword_candidate_count}")
        print(f"Duplicates Merged    : {hybrid_result.diagnostics.duplicate_candidate_count}")
        print(f"Excluded (below cap) : {hybrid_result.excluded_count}")
    elif not args.output:
        print(json.dumps(out_data, indent=2))

if __name__ == "__main__":
    main()
