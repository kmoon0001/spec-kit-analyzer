# --- Clinical/Biomedical NER Model Loading (offline-first with fallbacks) ---

# This list contains the names of the Hugging Face models that the application
# will attempt to load for Named Entity Recognition. The application will try
# to load the models in the order they are listed. If a model fails to load
# (e.g., due to no internet connection for a model that isn't cached), it will
# try the next one.
#
# The models should be compatible with the "token-classification" pipeline
# in the Hugging Face transformers library.

CLINICAL_NER_MODEL_CANDIDATES = [
    "OpenMed/OpenMed-NER-PathologyDetect-PubMed-v2-109M",
]