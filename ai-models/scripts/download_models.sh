#!/bin/bash
# Download base models script

set -e  # Exit on error

echo "====================================="
echo "Downloading AI Models for Sha8alny"
echo "====================================="
echo ""

# Create directories
mkdir -p models/base
cd models/base

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed"
    exit 1
fi

# 1. Download Sentence Transformers (small, fast)
echo "[1/3] Downloading Sentence Transformers (all-MiniLM-L6-v2)..."
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('sentence-transformers/all-MiniLM-L6-v2')
print('✓ Sentence Transformers downloaded (~90MB)')
"

# 2. Download Mistral 7B (7GB, takes ~30 min on good connection)
echo ""
echo "[2/3] Downloading Mistral 7B Instruct (~7GB)..."
echo "This may take 20-30 minutes depending on your internet speed..."
python -c "
from huggingface_hub import snapshot_download

model_name = 'mistralai/Mistral-7B-Instruct-v0.2'

snapshot_download(
    repo_id=model_name,
    local_dir='mistral-7b',
    local_dir_use_symlinks=False
)
print('✓ Mistral 7B downloaded (~7GB)')
"

# 3. Download LLaMA 3.1 8B (requires approval)
echo ""
echo "[3/3] Downloading LLaMA 3.1 8B Instruct (~8GB)..."
echo "Note: This requires Hugging Face access approval"
echo "Request access at: https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct"
echo ""

python -c "
from huggingface_hub import snapshot_download

model_name = 'meta-llama/Meta-Llama-3.1-8B-Instruct'

try:
    snapshot_download(
        repo_id=model_name,
        local_dir='llama-3.1-8b',
        local_dir_use_symlinks=False
    )
    print('✓ LLaMA 3.1 8B downloaded (~8GB)')
except Exception as e:
    print(f'✗ LLaMA download failed: {e}')
    print('You need to:')
    print('1. Go to https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct')
    print('2. Request access (usually approved in 1-2 hours)')
    print('3. Run: huggingface-cli login')
    print('4. Re-run this script')
    exit(1)
"

echo ""
echo "====================================="
echo "Download Complete!"
echo "====================================="
echo ""
echo "Models downloaded to: $(pwd)"
echo "Total size: ~14GB"
echo ""
echo "Next steps:"
echo "1. Activate your virtual environment"
echo "2. Test model loading with: python -c 'from src.llm import ModelLoader; ModelLoader.load_model_4bit(\"models/base/mistral-7b\")'"
