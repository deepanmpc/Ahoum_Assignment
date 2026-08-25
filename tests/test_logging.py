import pytest
from ahoum_assignment.logging_utils import redact_secrets, write_debug_artifact
from pathlib import Path

def test_redact_secrets():
    raw_text = "Here is my Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 token"
    safe_text = redact_secrets(raw_text)
    assert "eyJhbGci" not in safe_text
    assert "Bearer [REDACTED]" in safe_text
    
    raw_text_2 = "Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=="
    safe_text_2 = redact_secrets(raw_text_2)
    assert "QWxhZ" not in safe_text_2
    assert "Authorization: [REDACTED]" in safe_text_2
    
    raw_text_3 = '{"api_key": "sk-1234567890abcdef"}'
    safe_text_3 = redact_secrets(raw_text_3)
    assert "sk-12345" not in safe_text_3
    assert "[REDACTED]" in safe_text_3

def test_write_debug_artifact_creates_gitignore_and_redacts(tmp_path, monkeypatch):
    # Change working directory for test
    monkeypatch.chdir(tmp_path)
    
    secret_content = "Raw prompt with Bearer xyz123"
    write_debug_artifact("test_run", "prompt.txt", secret_content)
    
    debug_dir = Path("debug_artifacts")
    assert debug_dir.exists()
    assert (debug_dir / ".gitignore").exists()
    
    with open(debug_dir / ".gitignore", "r") as f:
        assert "*\n!.gitignore\n" in f.read()
        
    with open(debug_dir / "test_run" / "prompt.txt", "r") as f:
        content = f.read()
        assert "xyz123" not in content
        assert "Bearer [REDACTED]" in content
