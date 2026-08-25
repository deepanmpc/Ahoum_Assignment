import os
import subprocess
from pathlib import Path

import sys

def test_preprocessing_is_idempotent(tmp_path):
    root_dir = Path(__file__).resolve().parents[2]
    script_path = root_dir / "scripts" / "preprocess_facets.py"
    
    # Run 1
    result1 = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    assert result1.returncode == 0
    
    cat_path = root_dir / "data" / "processed" / "facet_catalogue.csv"
    audit_path = root_dir / "data" / "processed" / "facet_audit.md"
    
    assert cat_path.exists()
    assert audit_path.exists()
    
    with open(cat_path, "rb") as f:
        cat_run1 = f.read()
    with open(audit_path, "rb") as f:
        audit_run1 = f.read()
        
    # Run 2
    result2 = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    assert result2.returncode == 0
    
    with open(cat_path, "rb") as f:
        cat_run2 = f.read()
    with open(audit_path, "rb") as f:
        audit_run2 = f.read()
        
    # Verify byte-for-byte identical
    assert cat_run1 == cat_run2, "facet_catalogue.csv is not byte-identical across runs"
    assert audit_run1 == audit_run2, "facet_audit.md is not byte-identical across runs"
