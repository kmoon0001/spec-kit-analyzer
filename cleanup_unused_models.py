#!/usr/bin/env python3
"""
Remove unused models to optimize storage for clinical document analyzer.
"""

import os
import shutil
from pathlib import Path

def cleanup_unused_models():
    """Remove models not needed for clinical document analysis."""

    models_dir = Path("models")

    # Models to keep (essential for clinical analysis)
    keep_models = {
        "meditron7b",           # Primary medical model
        "biomedical-ner",       # Medical entity recognition
        "openmed-ner",          # Pathology detection
        "sentence-transformers-minilm",  # Document embeddings
        "dialogpt-medium",      # Chat assistant backup
        "models_index.json",    # Model index
        "confidence_calibrator.pkl"  # Calibration data
    }

    # Models to remove (not needed for clinical analysis)
    remove_models = {
        "dialogpt-small",       # Too basic
        "phi-2",               # Code-focused, not medical
        "flan-t5-base",        # General purpose
        "flan-t5-small",       # General purpose
    }

    print("Cleaning up unused models for clinical document analyzer...")
    print(f"Models directory: {models_dir.absolute()}")
    print()

    total_freed = 0
    removed_count = 0

    for model_name in remove_models:
        model_path = models_dir / model_name

        if model_path.exists():
            # Calculate size before removal
            model_size = 0
            for root, dirs, files in os.walk(model_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        model_size += os.path.getsize(file_path)
                    except (OSError, FileNotFoundError):
                        pass

            size_mb = model_size / (1024 * 1024)

            try:
                shutil.rmtree(model_path)
                total_freed += model_size
                removed_count += 1
                print(f"[REMOVED] {model_name} ({size_mb:.1f} MB)")
            except Exception as e:
                print(f"[ERROR] Failed to remove {model_name}: {e}")
        else:
            print(f"[SKIP] {model_name} not found")

    print(f"\nCleanup Summary:")
    print(f"  Models removed: {removed_count}")
    print(f"  Space freed: {total_freed / (1024**3):.2f} GB")
    print(f"  Remaining models: {len(keep_models)}")

    print(f"\nEssential models kept:")
    for model in keep_models:
        if (models_dir / model).exists():
            print(f"  ✓ {model}")
        else:
            print(f"  ✗ {model} (missing)")

if __name__ == "__main__":
    cleanup_unused_models()
