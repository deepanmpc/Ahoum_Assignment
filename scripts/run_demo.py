import json
import sys
from pathlib import Path

# Ensure local src/ can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ahoum_assignment.semantic_retriever import retrieve_semantic_candidates
from ahoum_assignment.keyword_router import KeywordRouter
from ahoum_assignment.hybrid_retriever import merge_retrieval_results
from ahoum_assignment.embeddings import FakeDeterministicEmbedder

def main():
    root = Path(__file__).resolve().parents[1]
    examples_file = root / "data" / "examples" / "dev_conversations.json"
    catalogue_csv = root / "data" / "processed" / "facet_catalogue.csv"
    rules_toml = root / "config" / "routing_rules.toml"
    npz_path = root / "data" / "processed" / "facet_embeddings.npz"
    meta_path = root / "data" / "processed" / "facet_index_metadata.json"
    
    with open(examples_file, 'r', encoding='utf-8') as f:
        conversations = json.load(f)
        
    try:
        import sentence_transformers
        embedder = sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")
        from ahoum_assignment.embeddings import SentenceTransformerEmbedder
        emb = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
    except ImportError:
        emb = FakeDeterministicEmbedder(dim=384)
        
    router = KeywordRouter(rules_toml, catalogue_csv)
    
    print("=== PHASE C ROUTING SANITY CHECK ===\n")
    
    for conv in conversations:
        print(f"[{conv['type'].upper()}] ID: {conv['id']}")
        print(f"TEXT: {conv['text']}")
        
        kw_result = router.retrieve(conv["text"])
        sem_result = retrieve_semantic_candidates(
            text=conv["text"],
            embedder=emb,
            npz_path=npz_path,
            meta_path=meta_path,
            catalogue_path=catalogue_csv,
            top_k=20,
            threshold=0.1
        )
        
        hybrid = merge_retrieval_results(
            sem_result, kw_result, semantic_weight=0.5, keyword_weight=0.5, hybrid_threshold=0.2, top_k=5
        )
        
        print("  Semantic Cands  :", sem_result.candidate_count)
        print("  Keyword Cands   :", kw_result.candidate_count)
        print("  Hybrid Cands    :", hybrid.candidate_count)
        print("  Excluded (Non-obs):", hybrid.diagnostics.excluded_non_observable_count)
        
        if not hybrid.candidates:
            print("  -> Shortlist empty! (Correct behavior for low-evidence)")
        else:
            for c in hybrid.candidates:
                print(f"  -> Rank {c.rank}: {c.facet_normalized} [{c.facet_category}] (Hybrid: {c.hybrid_score:.2f})")
                
        print("-" * 50)

if __name__ == "__main__":
    main()
