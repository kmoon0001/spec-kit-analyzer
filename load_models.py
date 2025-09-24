import os
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
import torch

# Check for the environment variable to skip downloads
if os.environ.get("SKIP_MODEL_DOWNLOAD", "false").lower() == "true":
    print("SKIP_MODEL_DOWNLOAD is set to true, skipping model downloads.")
    exit()

# --- 1. Load the NER Model ---
# This model is great for identifying medical entities.
print("Loading NER model...")
ner_model_name = "OpenMed/OpenMed-NER-PathologyDetect-PubMed-v2-109M"
ner_pipeline = pipeline("token-classification", model=ner_model_name, aggregation_strategy="simple")
print(f"NER model '{ner_model_name}' loaded successfully.")

# --- 2. Load the RAG Retriever Model ---
# This model is used to find relevant documents from your knowledge base.
print("\nLoading Retriever model...")
retriever_model_name = "pritamdeka/S-PubMedBert-MS-MARCO"
retriever = SentenceTransformer(retriever_model_name)
print(f"Retriever model '{retriever_model_name}' loaded successfully.")

# --- 3. Load the TinyLlama Generator Model ---
# This is the LLM that will generate answers and reports.
# We'll load it in 4-bit for efficiency.
print("\nLoading Generator LLM (TinyLlama)...")
generator_model_name = "nabilfaieaz/tinyllama-med-full"

# Load the tokenizer
generator_tokenizer = AutoTokenizer.from_pretrained(generator_model_name)

# Load the model with 4-bit quantization
generator_model = AutoModelForCausalLM.from_pretrained(
    generator_model_name,
    load_in_4bit=True,
    device_map="auto" # Automatically use GPU if available
)
print(f"Generator LLM '{generator_model_name}' loaded successfully.")

print("\nAll models loaded successfully! Your environment is ready.")

# You can now use these models for your application.
# Example NER usage:
text = "Patient has a history of hypertension and is prescribed aspirin."
entities = ner_pipeline(text)
print("\nExample NER output:")
print(entities)
