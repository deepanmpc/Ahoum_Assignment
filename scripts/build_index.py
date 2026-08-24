import sys
from pathlib import Path

# Ensure the local src/ package can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ahoum_assignment.semantic_index import build_index, check_index_freshness
from ahoum_assignment.embeddings import SentenceTransformerEmbedder, FakeDeterministicEmbedder

def main():
    root = Path(__file__).resolve().parents[1]
    catalogue_csv = root / "data" / "processed" / "facet_catalogue.csv"
    output_npz = root / "data" / "processed" / "facet_embeddings.npz"
    output_meta = root / "data" / "processed" / "facet_index_metadata.json"
    
    # Check if sentence-transformers is installed, if not fallback to Fake
    try:
        import sentence_transformers
        print("Using real SentenceTransformerEmbedder.")
        embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
    except ImportError:
        print("WARNING: sentence-transformers not installed. Using FakeDeterministicEmbedder for offline index.")
        embedder = FakeDeterministicEmbedder(dim=384)
    
    # Check freshness
    if check_index_freshness(catalogue_csv, output_meta, embedder.model_id):
        print("Index is up-to-date with catalogue and model ID. Skipping rebuild.")
        return
        
    print(f"Building semantic index...\nCatalogue: {catalogue_csv}\nOutput NPZ: {output_npz}\nModel ID: {embedder.model_id}")
    try:
        build_index(catalogue_csv, output_npz, output_meta, embedder)
        print("Success: Generated semantic vector index.")
    except Exception as e:
        print(f"Failed to build index: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
