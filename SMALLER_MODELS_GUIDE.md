# Smaller LLM Models Guide

## Current Model Issue

**Current**: Meditron-7B Q4_K_M (~4GB)
- **Problem**: Causing memory access violations with ctransformers
- **Status**: Currently using mocks to avoid crashes

## Recommended Smaller Alternatives

### Option 1: TinyLlama 1.1B (BEST FOR TESTING) ⭐
```yaml
models:
  generator: TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF
  generator_filename: tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
  generator_local_path: models/tinyllama
```
- **Size**: ~700MB
- **RAM**: 2-3GB required
- **Speed**: Very fast
- **Quality**: Good for basic compliance checks
- **Stability**: Excellent with ctransformers

### Option 2: Phi-2 2.7B (BALANCED)
```yaml
models:
  generator: TheBloke/phi-2-GGUF
  generator_filename: phi-2.Q4_K_M.gguf
  generator_local_path: models/phi2
```
- **Size**: ~1.6GB
- **RAM**: 4-5GB required
- **Speed**: Fast
- **Quality**: Better reasoning than TinyLlama
- **Stability**: Good

### Option 3: Mistral-7B-Instruct (QUALITY)
```yaml
models:
  generator: TheBloke/Mistral-7B-Instruct-v0.2-GGUF
  generator_filename: mistral-7b-instruct-v0.2.Q4_K_M.gguf
  generator_local_path: models/mistral7b
```
- **Size**: ~4GB (same as Meditron)
- **RAM**: 6-8GB required
- **Speed**: Moderate
- **Quality**: Excellent general reasoning
- **Stability**: Better than Meditron with ctransformers

### Option 4: Llama-3.2-1B (NEWEST SMALL MODEL)
```yaml
models:
  generator: bartowski/Llama-3.2-1B-Instruct-GGUF
  generator_filename: Llama-3.2-1B-Instruct-Q4_K_M.gguf
  generator_local_path: models/llama32-1b
```
- **Size**: ~800MB
- **RAM**: 2-3GB required
- **Speed**: Very fast
- **Quality**: Modern architecture, good performance
- **Stability**: Excellent

## Even Smaller Quantization Options

For any model above, you can use smaller quantizations:

### Q3_K_M (Smaller, slightly lower quality)
```yaml
generator_filename: model-name.Q3_K_M.gguf
```
- ~25% smaller than Q4_K_M
- Minimal quality loss

### Q2_K (Smallest, noticeable quality loss)
```yaml
generator_filename: model-name.Q2_K.gguf
```
- ~50% smaller than Q4_K_M
- More quality degradation

## Recommended Configuration for Your System

Based on the crashes, I recommend starting with **TinyLlama**:

```yaml
# config.yaml
use_ai_mocks: false  # Enable real AI

models:
  generator: TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF
  generator_filename: tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
  generator_local_path: models/tinyllama

llm:
  context_length: 2048  # Reduced from 4096
  gpu_layers: 0
  threads: 4  # Reduced from 6
  model_type: ctransformers
  generation_params:
    max_new_tokens: 512  # Reduced from 1024
    temperature: 0.1
    top_p: 0.9
```

## How to Switch Models

### Step 1: Update config.yaml
Edit the `models` section with your chosen model configuration.

### Step 2: Clear old model cache (optional)
```batch
rmdir /s /q models
mkdir models
```

### Step 3: Restart the application
```batch
LAUNCH_COMPLETE_APP.bat
```

The model will download automatically on first use.

## Testing Model Stability

### Test with TinyLlama first:
```batch
# 1. Update config.yaml with TinyLlama settings
# 2. Set use_ai_mocks: false
# 3. Run test
START_API_ONLY.bat
python test_analysis_direct.py
```

If it works, you can try larger models. If it crashes, stay with mocks or try an even smaller quantization.

## Alternative: Use Transformers Backend

If ctransformers keeps crashing, switch to transformers backend:

```yaml
llm:
  model_type: transformers  # Instead of ctransformers

models:
  generator: microsoft/phi-2
  generator_filename: ""  # Not needed for transformers
```

This uses HuggingFace transformers library which is more stable but slower.

## Memory Requirements Summary

| Model | Size | RAM Needed | Speed | Quality | Stability |
|-------|------|------------|-------|---------|-----------|
| TinyLlama 1.1B Q4 | 700MB | 2-3GB | ⚡⚡⚡ | ⭐⭐⭐ | ✅✅✅ |
| Llama-3.2-1B Q4 | 800MB | 2-3GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | ✅✅✅ |
| Phi-2 Q4 | 1.6GB | 4-5GB | ⚡⚡ | ⭐⭐⭐⭐ | ✅✅ |
| Mistral-7B Q4 | 4GB | 6-8GB | ⚡ | ⭐⭐⭐⭐⭐ | ✅✅ |
| Meditron-7B Q4 | 4GB | 6-8GB | ⚡ | ⭐⭐⭐⭐⭐ | ⚠️ (crashes) |

## Current Status

✅ **Mocks Enabled**: Application works perfectly with mock AI
⚠️ **Real AI**: Meditron-7B crashes, needs smaller alternative
🎯 **Recommendation**: Try TinyLlama first, then upgrade if stable

## Quick Switch to TinyLlama

I can create a config file for you. Want me to create `config_tinyllama.yaml`?
