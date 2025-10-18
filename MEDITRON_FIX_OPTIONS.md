# Making Meditron-7B Work - All Options

## The Real Problem

**ctransformers** library has memory access violations with Meditron-7B GGUF files on Windows. This is a known issue with the library, not your system.

## Option 1: Switch to Transformers Backend (Recommended) ⭐

Instead of ctransformers, use HuggingFace transformers directly:

```yaml
llm:
  model_type: transformers  # Changed from ctransformers

models:
  generator: epfl-llm/meditron-7b  # Original model, not GGUF
  generator_filename: ""  # Not needed for transformers
  generator_local_path: models/meditron7b
```

**Pros:**
- ✅ More stable than ctransformers
- ✅ Official HuggingFace support
- ✅ Better error handling

**Cons:**
- ⚠️ Slower than GGUF (no quantization)
- ⚠️ Uses more RAM (~14GB for full model)
- ⚠️ Larger download (~13GB vs 4GB)

---

## Option 2: Use llama.cpp Server

Run Meditron through llama.cpp server instead of ctransformers:

### Step 1: Download llama.cpp
```bash
# From: https://github.com/ggerganov/llama.cpp/releases
# Get: llama-b{version}-bin-win-avx2-x64.zip
```

### Step 2: Run Server
```bash
llama-server.exe -m meditron-7b.Q4_K_M.gguf --port 8080 --host 127.0.0.1
```

### Step 3: Modify Code
Point your LLMService to use OpenAI-compatible API at `http://localhost:8080`

**Pros:**
- ✅ More stable than ctransformers
- ✅ Uses GGUF (quantized, smaller)
- ✅ Better performance

**Cons:**
- ⚠️ Requires code changes
- ⚠️ Extra process to manage

---

## Option 3: Use Ollama (Easiest) 🎯

Ollama has better GGUF support than ctransformers:

### Step 1: Install Ollama
Download from: https://ollama.ai

### Step 2: Create Modelfile
```dockerfile
# Modelfile
FROM ./meditron-7b.Q4_K_M.gguf

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER stop "</analysis>"
PARAMETER stop "\n\n---"
```

### Step 3: Import Model
```bash
ollama create meditron -f Modelfile
ollama run meditron
```

### Step 4: Modify Code
Use Ollama's API at `http://localhost:11434`

**Pros:**
- ✅ Most stable GGUF support
- ✅ Easy to manage
- ✅ Good performance
- ✅ Works with your existing GGUF file

**Cons:**
- ⚠️ Requires code changes
- ⚠️ Extra software to install

---

## Option 4: Try Different Quantization

Sometimes different quantizations work better:

```yaml
# Try Q5_K_M instead of Q4_K_M
generator_filename: meditron-7b.Q5_K_M.gguf

# Or try Q3_K_M (smaller)
generator_filename: meditron-7b.Q3_K_M.gguf
```

**Pros:**
- ✅ No code changes
- ✅ Quick to test

**Cons:**
- ⚠️ May still crash
- ⚠️ Not guaranteed to work

---

## Option 5: Use LM Studio

GUI application with better GGUF support:

### Step 1: Install LM Studio
Download from: https://lmstudio.ai

### Step 2: Load Meditron
- Import your meditron-7b.Q4_K_M.gguf
- Start local server

### Step 3: Modify Code
Point to LM Studio's API (usually port 1234)

**Pros:**
- ✅ GUI interface
- ✅ Better stability than ctransformers
- ✅ Easy to use

**Cons:**
- ⚠️ Requires code changes
- ⚠️ Extra software

---

## My Recommendation

### For Keeping Meditron:

**Best: Use Ollama** (Option 3)
1. Install Ollama
2. Import your existing Meditron GGUF
3. Modify LLMService to use Ollama API
4. More stable than ctransformers

### Alternative: Use Transformers Backend (Option 1)
1. Change `model_type: transformers` in config
2. Download full Meditron model
3. Slower but more stable

### Easiest: Switch to Llama 3.2 3B
- Modern model
- Works with ctransformers
- Good medical reasoning
- No code changes needed

---

## Code Changes for Ollama/llama.cpp

If you want to use Ollama or llama.cpp, I can modify `LLMService` to support OpenAI-compatible APIs:

```python
# Add to LLMService
def __init__(self, ..., use_api_server=False, api_url=None):
    if use_api_server:
        self.backend = "openai_compatible"
        self.api_url = api_url or "http://localhost:11434"
    else:
        # existing ctransformers code
```

Then in config:
```yaml
llm:
  model_type: openai_compatible
  api_url: http://localhost:11434  # Ollama
  # or http://localhost:8080  # llama.cpp
```

---

## Bottom Line

**ctransformers + Meditron = Known Issue**

Your options:
1. ✅ **Use Ollama** - Best stability with GGUF
2. ✅ **Use Transformers** - More stable, but slower
3. ✅ **Switch to Llama 3.2 3B** - Works with ctransformers
4. ⚠️ **Try different quantization** - May not work

**Want me to implement Ollama support?** I can modify the code to work with Ollama's API, then you can use Meditron through Ollama instead of ctransformers.
