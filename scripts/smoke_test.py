import csv
import json
import shutil
import sys
from pathlib import Path

# Setup paths to ensure we can import ahoum_assignment
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ahoum_assignment.preprocessing import process_file
from ahoum_assignment.semantic_index import build_index
from ahoum_assignment.embeddings import FakeDeterministicEmbedder
from ahoum_assignment.keyword_router import KeywordRouter
from ahoum_assignment.semantic_retriever import retrieve_semantic_candidates
from ahoum_assignment.hybrid_retriever import merge_retrieval_results
from ahoum_assignment.scoring_service import score_conversation
from ahoum_assignment.result_aggregator import aggregate_results
from ahoum_assignment.providers.base import BaseProvider, ProviderResponse

class SmokeMockProvider(BaseProvider):
    @property
    def provider_name(self) -> str: return "smoke-mock"
    @property
    def model_name(self) -> str: return "smoke-eval"
    def generate(self, prompt: str) -> ProviderResponse:
        import re
        ids = re.findall(r"facet_id: (\S+)", prompt)
        results = [{
            "facet_id": fid,
            "status": "scored",
            "score_1_to_5": 5,
            "confidence_0_to_1": 0.95,
            "evidence_quote": "very careful",
            "reason": "smoke reason"
        } for fid in ids]
        return ProviderResponse(
            text=json.dumps({"results": results}),
            provider_name=self.provider_name,
            model_name=self.model_name,
            latency_ms=5.0
        )

def main():
    print("--- Starting Deterministic E2E Smoke Test ---")
    root = Path(__file__).resolve().parents[1]
    
    # 0. Setup Fixtures
    fixture_dir = root / "tests" / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    
    raw_csv = fixture_dir / "smoke_raw.csv"
    with open(raw_csv, "w", encoding="utf-8") as f:
        f.write("Facets\n")
        f.write("Meticulous and careful\n")
        f.write("Meticulous and careful\n")
        f.write("Speaks clearly\n")
        f.write("Has asthma\n")
        
    overrides_csv = fixture_dir / "facet_overrides.csv"
    with open(overrides_csv, "w", encoding="utf-8") as f:
        f.write("facet_normalized,facet_category,facet_type,conversation_observable,observability_reason,sensitivity,abstention_reason,review_required\n")
        f.write("meticulous and careful,work_habits,conversational_trait,true,Test,normal,,false\n")
        f.write("speaks clearly,communication,conversational_trait,true,Test,normal,,false\n")
        f.write("has asthma,health_medical,medical_or_diagnostic,false,Test,sensitive,Privacy,false\n")
        
    anchor_csv = fixture_dir / "anchor_overrides.csv"
    with open(anchor_csv, "w", encoding="utf-8") as f:
        f.write("facet_normalized,scoring_definition,anchor_1,anchor_3,anchor_5\n")
        
    rules_toml = fixture_dir / "smoke_rules.toml"
    with open(rules_toml, "w", encoding="utf-8") as f:
        f.write('[categories.work_habits]\nkeywords = ["careful"]\n')
        
    out_dir = root / "data" / "outputs" / "smoke_test_run"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    processed_csv = out_dir / "smoke_catalogue.csv"
    idx_npz = out_dir / "smoke_index.npz"
    idx_meta = out_dir / "smoke_meta.json"
    
    # 1. Preprocessing
    print("1. Running Preprocessing...")
    process_file(raw_csv, processed_csv)
    assert processed_csv.exists(), "Processed CSV was not created"
    
    # 2. Index Building
    print("2. Building Semantic Index...")
    embedder = FakeDeterministicEmbedder(dim=384)
    build_index(processed_csv, idx_npz, idx_meta, embedder)
    assert idx_npz.exists() and idx_meta.exists(), "Index files were not created"
    
    # 3. Retrieval
    print("3. Running Hybrid Retrieval...")
    test_text = "I am very careful when I work."
    kw_router = KeywordRouter(rules_toml, processed_csv)
    kw_res = kw_router.retrieve(test_text, conversation_id="smoke-1")
    
    sem_res = retrieve_semantic_candidates(
        text=test_text,
        embedder=embedder,
        npz_path=idx_npz,
        meta_path=idx_meta,
        catalogue_path=processed_csv,
        top_k=5,
        conversation_id="smoke-1"
    )
    
    hybrid_res = merge_retrieval_results(sem_res, kw_res, semantic_weight=0.5, keyword_weight=0.5, hybrid_threshold=0.1, top_k=5)
    
    # Ensure unobservable facet (asthma) is EXCLUDED
    for c in hybrid_res.candidates:
        assert c.facet_category != "health_medical", "Unsafe facet was not excluded!"
        
    print(f"   -> Retrieved {hybrid_res.candidate_count} candidates safely.")
    
    # 4. Scoring
    print("4. Running Batched Scoring...")
    provider = SmokeMockProvider()
    score_res = score_conversation(
        conversation_id="smoke-1",
        conversation_text=test_text,
        retrieval_result=hybrid_res,
        provider=provider,
        catalogue_path=processed_csv,
        batch_size=5,
        dry_run=False
    )
    
    agg_res = aggregate_results(hybrid_res, score_res)
    if agg_res.scored_count == 0:
        print("AGG REG:", agg_res)
    assert agg_res.scored_count > 0, f"No facets were scored. AggRes: {agg_res}"
    
    print("--- Smoke Test Passed Successfully ---")

if __name__ == "__main__":
    main()
