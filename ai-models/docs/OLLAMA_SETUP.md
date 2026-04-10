# Ollama Setup Guide for Sha8alny Advisory

This guide helps you set up Ollama for local LLM inference in the advisory module.

## What is Ollama?

Ollama is a lightweight tool to run LLMs locally on your machine. It's like Docker for language models - easy to install, pull models, and run inference without cloud APIs or costs.

**Why Ollama for Sha8alny?**
- **Free**: No API costs, runs entirely on your machine
- **Fast**: Local inference, no network latency
- **Private**: User data never leaves your machine
- **Simple**: One command to install, one to run

---

## Installation

### macOS (Recommended)
```bash
# Using Homebrew
brew install ollama

# OR download from website
# Visit: https://ollama.ai/download
```

### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Windows
Download installer from: https://ollama.ai/download

---

## Quick Start

### 1. Start Ollama Server
```bash
# Start the Ollama service (runs in background)
ollama serve
```

This starts the API server at `http://localhost:11434`

### 2. Pull Mistral 7B Model
```bash
# Download the model (~4GB)
ollama pull mistral

# Verify it's installed
ollama list
```

Expected output:
```
NAME              ID              SIZE     MODIFIED
mistral:latest    abc123...       4.1 GB   Just now
```

### 3. Test the Model
```bash
# Quick test
ollama run mistral "Hello, how are you?"

# Interactive chat mode
ollama run mistral
>>> How do I become a software engineer?
```

---

## API Usage

Ollama exposes a REST API at `http://localhost:11434`

### Generate Response (Used by Sha8alny)
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt": "How do I become a software engineer?",
  "stream": false
}'
```

### Python Usage
```python
import requests

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "mistral",
        "prompt": "How do I become a software engineer?",
        "stream": False
    }
)
result = response.json()
print(result["response"])
```

---

## Model Options

| Model | Size | Best For |
|-------|------|----------|
| `mistral` | 4.1 GB | General purpose, good for career advice (recommended) |
| `llama3.2` | 2-4 GB | Lighter, faster responses |
| `mistral-openorca` | 4.1 GB | Better instruction following |

**For Sha8alny**: We use `mistral` as it balances quality and speed.

---

## Troubleshooting

### "Connection refused"
Ollama server not running. Start it:
```bash
ollama serve
```

### "Model not found"
Pull the model first:
```bash
ollama pull mistral
```

### Slow responses
- First response is slow (model loading)
- Subsequent responses are faster
- Consider: `llama3.2:1b` for faster but less accurate responses

### Memory issues
Mistral needs ~8GB RAM. If memory is tight:
```bash
ollama pull llama3.2:1b  # Smaller 1B model
```

---

## Running as Service (Auto-start)

### macOS
```bash
# Ollama auto-starts after installation
# Check status:
launchctl list | grep ollama
```

### Linux (systemd)
```bash
sudo systemctl enable ollama
sudo systemctl start ollama
sudo systemctl status ollama
```

---

## Integration with Django Backend

The Django backend calls Ollama at `http://localhost:11434`. Make sure:

1. ✅ Ollama server is running before starting Django
2. ✅ Mistral model is downloaded
3. ✅ Port 11434 is not blocked

Test from Django environment:
```bash
cd Backend
source venv/bin/activate
python -c "import requests; print(requests.get('http://localhost:11434/api/version').json())"
```

---

## Next Steps

After Ollama is running:
1. The `generator.py` module will connect to it
2. Advisory API will use it for responses
3. You can test with: `python ai-models/src/rag/generator.py`

---

**Ollama Documentation**: https://ollama.ai/docs
**Mistral Model Info**: https://ollama.ai/library/mistral
