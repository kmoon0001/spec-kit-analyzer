# Python
import os

# Choose a cache directory (env var first, else local folder)
CACHE_DIR = os.environ.get("HF_CACHE", os.path.join(os.getcwd(), "hf-model-cache"))
os.makedirs(CACHE_DIR, exist_ok=True)

print(f"Using cache dir: {CACHE_DIR}")

# 1) Clinical NER candidates
try:
    from CLINICAL_NER_MODEL_CANDIDATES import CLINICAL_NER_MODEL_CANDIDATES
    candidates = list(CLINICAL_NER_MODEL_CANDIDATES)
except Exception:
    # Fallback list if your module is unavailable here; adjust as needed
    candidates = [
        "d4data/biomedical-ner-all",
        # add other model IDs you plan to use
    ]

from transformers import AutoTokenizer, AutoModelForTokenClassification

ok = []
failed = []

for name in candidates:
    try:
        print(f"Seeding Clinical NER model: {name}")
        tok = AutoTokenizer.from_pretrained(name, cache_dir=CACHE_DIR)
        mdl = AutoModelForTokenClassification.from_pretrained(name, cache_dir=CACHE_DIR)
        ok.append(name)
    except Exception as e:
        print(f"Failed to seed {name}: {e}")
        failed.append((name, str(e)))

# 2) Sentence-Transformers model for semantic analysis
try:
    print("Seeding sentence-transformers model: all-MiniLM-L6-v2")
    from sentence_transformers import SentenceTransformer
    SentenceTransformer("all-MiniLM-L6-v2", cache_folder=CACHE_DIR)
    st_ok = True
except Exception as e:
    print(f"Failed to seed all-MiniLM-L6-v2: {e}")
    st_ok = False

print("\nSummary")
print("Seeded Clinical NER:", ok)
print("Failed Clinical NER:", failed)
print("Sentence-Transformers OK:", st_ok)
print(f"Cache ready at: {CACHE_DIR}")