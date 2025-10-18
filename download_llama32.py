"""Download Llama 3.2 3B Instruct model"""
import os
from pathlib import Path

def download_model():
    """Download Llama 3.2 3B GGUF model"""
    try:
        from huggingface_hub import hf_hub_download

        print("=" * 60)
        print("Downloading Llama 3.2 3B Instruct (Q4_K_M)")
        print("=" * 60)
        print()
        print("Repository: bartowski/Llama-3.2-3B-Instruct-GGUF")
        print("File: Llama-3.2-3B-Instruct-Q4_K_M.gguf")
        print("Size: ~2GB")
        print()
        print("This may take 5-10 minutes depending on your connection...")
        print()

        # Create models directory
        models_dir = Path("models/llama32-3b")
        models_dir.mkdir(parents=True, exist_ok=True)

        # Download the model
        model_path = hf_hub_download(
            repo_id="bartowski/Llama-3.2-3B-Instruct-GGUF",
            filename="Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            local_dir=str(models_dir),
            local_dir_use_symlinks=False,
            resume_download=True
        )

        print()
        print("=" * 60)
        print("✓ Download Complete!")
        print("=" * 60)
        print()
        print(f"Model saved to: {model_path}")
        print()
        print("Next steps:")
        print("1. Run: LAUNCH_COMPLETE_APP.bat")
        print("2. Or test with: START_API_ONLY.bat")
        print()

        return True

    except ImportError:
        print("ERROR: huggingface_hub not installed")
        print()
        print("Installing huggingface_hub...")
        import subprocess
        subprocess.check_call(["pip", "install", "huggingface_hub"])
        print()
        print("Please run this script again.")
        return False

    except Exception as e:
        print(f"ERROR: Download failed: {e}")
        print()
        print("You can download manually from:")
        print("https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF")
        print()
        print("Download: Llama-3.2-3B-Instruct-Q4_K_M.gguf")
        print("Save to: models/llama32-3b/")
        return False

if __name__ == "__main__":
    download_model()
