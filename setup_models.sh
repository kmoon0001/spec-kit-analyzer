#!/bin/bash

MODEL_DIR="./models"

mkdir -p $MODEL_DIR

# Download ClinicalBERT from Hugging Face
transformers-cli download --model emilyalsentzer/Bio_ClinicalBERT --cache_dir $MODEL_DIR

# Download BioBERT from Hugging Face
transformers-cli download --model dmis-lab/biobert-base-cased-v1.1 --cache_dir $MODEL_DIR

# Download AraG (replace with actual Hugging Face model path if needed)
transformers-cli download --model arag-chat-model/test-release --cache_dir $MODEL_DIR

echo "Models downloaded to $MODEL_DIR"
