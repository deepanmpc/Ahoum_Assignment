#!/usr/bin/env bash
set -euo pipefail

echo "============================================"
echo "  Ahoum Assignment — Full Pipeline Demo"
echo "============================================"
echo ""

# 1. Setup
if [ ! -d ".venv" ]; then
    echo "[1/7] Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "Installing dependencies (this may take a moment)..."
    pip install -q -e '.[dev]'
else
    echo "[1/7] Virtual environment exists. Skipping dependency installation."
    source .venv/bin/activate
fi

# 2. Doctor check
echo ""
echo "[2/7] Running doctor check..."
python scripts/doctor.py doctor

# 3. Preprocess facets
echo ""
echo "[3/7] Preprocessing raw facets..."
python scripts/preprocess_facets.py

# 4. Build semantic index
echo ""
echo "[4/7] Building semantic embedding index..."
python scripts/build_index.py

# 5. Run tests
echo ""
echo "[5/7] Running test suite..."
python -m pytest tests/ -q

# 6. Hybrid retrieval demo
echo ""
echo "[6/7] Hybrid retrieval examples..."
echo ""

echo "--- Emotional regulation query ---"
python scripts/retrieve_facets.py \
    --text "I waited calmly even though the customer was extremely rude. I took a deep breath and responded politely." \
    --top-k 5 --human
echo ""

echo "--- Finance/risk query ---"
python scripts/retrieve_facets.py \
    --text "I strictly budget my savings and avoid any serious investment risk or gambling." \
    --top-k 5 --human
echo ""

echo "--- Hallucination bait (should exclude medical/religious) ---"
python scripts/retrieve_facets.py \
    --text "My blood pressure is high because of my daily church prayer and disease diagnosis." \
    --top-k 5 --human
echo ""

# 7. Dry-run scoring
echo "[7/7] Dry-run scoring demo..."
echo ""

echo "--- Direct evidence conversation ---"
python scripts/score_conversation.py \
    --text "I waited calmly even though the customer was extremely rude. I took a deep breath and responded politely." \
    --dry-run --human
echo ""

echo "--- Low evidence conversation ---"
python scripts/score_conversation.py \
    --text "Hey, nice weather today. Want to grab coffee?" \
    --dry-run --human
echo ""

echo "============================================"
echo "  Pipeline complete. All steps succeeded."
echo "============================================"
echo ""
echo "To run with a live Ollama model instead of dry-run:"
echo "  ollama pull qwen2.5:3b-instruct"
echo "  python scripts/score_conversation.py --text \"your text\" --human"
echo ""
echo "To use a cloud provider:"
echo "  export AHOUM_MODEL_PROVIDER=groq"
echo "  export GROQ_API_KEY=your-key"
echo "  export AHOUM_MODEL_NAME=llama-3.1-8b-instant"
echo "  python scripts/score_conversation.py --text \"your text\" --human"
