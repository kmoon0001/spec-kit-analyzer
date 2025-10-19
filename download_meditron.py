#!/usr/bin/env python3
"""
Download Meditron 7B GGUF model for therapy compliance analysis.
"""

import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download

def download_meditron():
    """Download Meditron 7B Q4_K_M GGUF model."""

    print("Downloading Meditron 7B for medical compliance analysis...")

    # Model details
    repo_id = "TheBloke/meditron-7B-GGUF"
    filename = "meditron-7b.Q4_K_M.gguf"
    local_dir = Path("models/meditron7b")

    # Ensure directory exists
    local_dir.mkdir(parents=True, exist_ok=True)

    try:
        print(f"Downloading {filename} from {repo_id}...")
        print("This may take several minutes (model is ~4GB)...")

        # Download the model
        model_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=local_dir,
            local_dir_use_symlinks=False
        )

        print(f"Successfully downloaded Meditron 7B!")
        print(f"Model saved to: {model_path}")
        print(f"Model size: ~4GB")
        print(f"Ready for medical compliance analysis!")

        return True

    except Exception as e:
        print(f"Error downloading Meditron: {e}")
        print("Alternative: Use BioGPT or keep mocks enabled")
        return False

if __name__ == "__main__":
    success = download_meditron()
    sys.exit(0 if success else 1)
