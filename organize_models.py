#!/usr/bin/env python3
"""
Organize language models by moving them from HuggingFace cache to local models folder.
"""

import os
import shutil
from pathlib import Path
import json

def organize_models():
    """Move important models from HuggingFace cache to local models folder."""

    # Paths
    hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
    local_models = Path("models")

    # Ensure local models directory exists
    local_models.mkdir(exist_ok=True)

    # Models to organize (priority order)
    models_to_move = [
        {
            "cache_name": "models--microsoft--DialoGPT-medium",
            "local_name": "dialogpt-medium",
            "description": "DialoGPT Medium - Conversational AI"
        },
        {
            "cache_name": "models--microsoft--DialoGPT-small",
            "local_name": "dialogpt-small",
            "description": "DialoGPT Small - Lightweight conversational"
        },
        {
            "cache_name": "models--microsoft--phi-2",
            "local_name": "phi-2",
            "description": "Microsoft Phi-2 - Code and reasoning"
        },
        {
            "cache_name": "models--google--flan-t5-base",
            "local_name": "flan-t5-base",
            "description": "Google Flan-T5 Base - Instruction following"
        },
        {
            "cache_name": "models--google--flan-t5-small",
            "local_name": "flan-t5-small",
            "description": "Google Flan-T5 Small - Lightweight instruction"
        },
        {
            "cache_name": "models--sentence-transformers--all-MiniLM-L6-v2",
            "local_name": "sentence-transformers-minilm",
            "description": "Sentence Transformers - Embeddings"
        },
        {
            "cache_name": "models--d4data--biomedical-ner-all",
            "local_name": "biomedical-ner",
            "description": "Biomedical NER - Medical entity recognition"
        },
        {
            "cache_name": "models--OpenMed--OpenMed-NER-PathologyDetect-PubMed-v2-109M",
            "local_name": "openmed-ner",
            "description": "OpenMed NER - Pathology detection"
        }
    ]

    print("Organizing language models...")
    print(f"HuggingFace Cache: {hf_cache}")
    print(f"Local Models: {local_models}")
    print()

    moved_models = []

    for model_info in models_to_move:
        cache_path = hf_cache / model_info["cache_name"]
        local_path = local_models / model_info["local_name"]

        if cache_path.exists():
            print(f"Moving {model_info['description']}...")

            # Create local directory
            local_path.mkdir(exist_ok=True)

            # Copy model files
            try:
                for item in cache_path.rglob("*"):
                    if item.is_file():
                        relative_path = item.relative_to(cache_path)
                        target_path = local_path / relative_path
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target_path)

                # Create model info file
                info_file = local_path / "model_info.json"
                with open(info_file, 'w') as f:
                    json.dump({
                        "name": model_info["local_name"],
                        "description": model_info["description"],
                        "original_cache": model_info["cache_name"],
                        "moved_from": str(cache_path)
                    }, f, indent=2)

                moved_models.append(model_info)
                print(f"  [OK] Moved to: {local_path}")

            except Exception as e:
                print(f"  [ERROR] Error moving {model_info['local_name']}: {e}")
        else:
            print(f"  - {model_info['description']} not found in cache")

    print(f"\nSummary:")
    print(f"  Models moved: {len(moved_models)}")
    print(f"  Local models folder: {local_models.absolute()}")

    # Create models index
    index_file = local_models / "models_index.json"
    with open(index_file, 'w') as f:
        json.dump({
            "models": moved_models,
            "total_count": len(moved_models),
            "organized_at": str(Path.cwd())
        }, f, indent=2)

    print(f"  Models index: {index_file}")
    print("\nNext steps:")
    print("  1. Update config.yaml to use local model paths")
    print("  2. Test model loading from local paths")
    print("  3. Consider removing HuggingFace cache to save space")

if __name__ == "__main__":
    organize_models()
