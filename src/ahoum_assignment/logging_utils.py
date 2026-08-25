import logging
import re
import os
from pathlib import Path

def setup_logger(name: str, debug_mode: bool = False) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    return logger

def redact_secrets(text: str) -> str:
    """Redact common API keys, Bearer tokens, and Authorization headers."""
    if not text:
        return text
    # Redact Bearer tokens
    text = re.sub(r'(?i)(bearer\s+)[A-Za-z0-9\-\._~+/]+=*', r'\1[REDACTED]', text)
    # Redact Authorization headers
    text = re.sub(r'(?i)(authorization:\s*)[^\n\r]+', r'\1[REDACTED]', text)
    text = re.sub(r'(?i)(api_key[\s=:"]+)[A-Za-z0-9\-\._~+/]+=*', r'\1[REDACTED]', text)
    return text

def write_debug_artifact(run_id: str, artifact_name: str, content: str):
    """Write raw debug artifacts locally if enabled. Never leaks to standard output."""
    debug_dir = Path("debug_artifacts") / run_id
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure debug_dir is git-ignored
    ignore_file = Path("debug_artifacts") / ".gitignore"
    if not ignore_file.exists():
        Path("debug_artifacts").mkdir(exist_ok=True)
        with open(ignore_file, "w") as f:
            f.write("*\n!.gitignore\n")
            
    # Redact secrets before writing even to debug dir
    safe_content = redact_secrets(content)
    
    with open(debug_dir / artifact_name, "w", encoding="utf-8") as f:
        f.write(safe_content)
