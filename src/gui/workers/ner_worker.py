import torch
from PyQt6.QtCore import QObject, pyqtSignal
from transformers import pipeline

from src.CLINICAL_NER_MODEL_CANDIDATES import CLINICAL_NER_MODEL_CANDIDATES
from src.entity import NEREntity

class NERWorker(QObject):
    """
    A worker QObject for running Named Entity Recognition in a separate thread.
    """
    finished = pyqtSignal(list)  # Emits a list of NEREntity objects
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)  # Progress percentage and message

    def __init__(self, text: str):
        super().__init__()
        self.text = text
        self._cancel = False
        self.ner_pipeline = None

    def cancel(self):
        """Requests cancellation of the NER process."""
        self._cancel = True

    def _load_model(self):
        """Loads the NER model and tokenizer."""
        self.progress.emit(10, "Loading NER model...")
        for model_name in CLINICAL_NER_MODEL_CANDIDATES:
            if self._cancel:
                return False
            try:
                # Using a specific torch_dtype and device_map for efficiency
                self.ner_pipeline = pipeline(
                    "token-classification",
                    model=model_name,
                    aggregation_strategy="simple",
                    torch_dtype=torch.bfloat16,
                    device_map="auto" # Automatically use GPU if available
                )
                self.progress.emit(25, f"Successfully loaded NER model '{model_name}'.")
                return True
            except Exception as e:
                self.progress.emit(25, f"Failed to load '{model_name}': {e}")
        return False

    def run(self):
        """
        Runs the NER pipeline on the text and emits the results.
        """
        if not self._load_model():
            if not self._cancel:
                self.error.emit("Could not load any NER models. Check connection or cache.")
            else:
                self.error.emit("NER operation canceled during model loading.")
            return

        if self._cancel or self.ner_pipeline is None:
            self.error.emit("NER operation canceled before analysis.")
            return

        self.progress.emit(50, "Analyzing text for named entities...")

        try:
            results = self.ner_pipeline(self.text)

            if self._cancel:
                self.error.emit("NER operation canceled during analysis.")
                return

            entities = [
                NEREntity(
                    text=item['word'],
                    label=item['entity_group'],
                    score=float(item['score']),
                    start=item['start'],
                    end=item['end']
                ) for item in results
            ]

            self.progress.emit(100, "NER analysis complete.")
            self.finished.emit(entities)

        except Exception as e:
            self.error.emit(f"An error occurred during NER analysis: {e}")
