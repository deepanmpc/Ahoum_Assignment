import argparse
import json
import sys
from pathlib import Path

# Ensure the local src/ package can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ahoum_assignment.semantic_retriever import retrieve_semantic_candidates
from ahoum_assignment.embeddings import FakeDeterministicEmbedder, SentenceTransformerEmbedder


def main():
    parser = argparse.ArgumentParser(description="Runtime Semantic Retrieval CLI")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Direct conversation text input")
    group.add_argument("--file", type=str, help="Text file input path")
    
    parser.add_argument("--top-k", type=int, default=10, help="Maximum number of candidates to retrieve")
    parser.add_argument("--threshold", type=float, default=0.5, help="Minimum cosine similarity threshold")
    parser.add_argument("--output", type=str, help="Optional JSON output path")
    parser.add_argument("--config", type=str, help="Optional config path (unused placeholder)")
    
    args = parser.parse_args()
    
    # Read text keeping it entirely local
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
    npz_path = root / "data" / "processed" / "facet_embeddings.npz"
    meta_path = root / "data" / "processed" / "facet_index_metadata.json"
    
    # Use real embedder if available, otherwise fallback
    try:
        import sentence_transformers
        embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
    except ImportError:
        embedder = FakeDeterministicEmbedder(dim=384)
        
    try:
        result = retrieve_semantic_candidates(
            text=text,
            embedder=embedder,
            npz_path=npz_path,
            meta_path=meta_path,
            catalogue_path=catalogue_csv,
            top_k=args.top_k,
            threshold=args.threshold
        )
    except Exception as e:
        print(f"Retrieval Error: {e}")
        sys.exit(1)
        
    out_data = result.model_dump()
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(out_data, f, indent=2)
        print(f"Results successfully written to {args.output}")
    else:
        print(json.dumps(out_data, indent=2))


if __name__ == "__main__":
    main()
