from PyQt6.QtCore import QObject, pyqtSignal
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
import torch

class ModelCheckWorker(QObject):
    """
    A worker that sequentially loads all AI models to verify the environment.
    """
    finished = pyqtSignal(str, bool)  # Emits a final status message and a success flag
    progress = pyqtSignal(str)      # Emits progress updates

    def __init__(self):
        super().__init__()
        self.models = {
            "NER": "OpenMed/OpenMed-NER-PathologyDetect-PubMed-v2-109M",
            "Retriever": "pritamdeka/S-PubMedBert-MS-MARCO",
            "Generator": "nabilfaieaz/tinyllama-med-full",
        }

    def run(self):
        """
        Tries to load each model and reports success or the first failure.
        """
        self.progress.emit("Starting model check...")

        # Check NER Model
        try:
            self.progress.emit(f"Checking NER model: {self.models['NER']}...")
            pipeline("token-classification", model=self.models['NER'], aggregation_strategy="simple")
            self.progress.emit("NER model check: OK")
        except Exception as e:
            self.finished.emit(f"Failed to load NER model: {e}", False)
            return

        # Check Retriever Model
        try:
            self.progress.emit(f"Checking Retriever model: {self.models['Retriever']}...")
            SentenceTransformer(self.models['Retriever'])
            self.progress.emit("Retriever model check: OK")
        except Exception as e:
            self.finished.emit(f"Failed to load Retriever model: {e}", False)
            return

        # Check Generator Model
        try:
            self.progress.emit(f"Checking Generator model: {self.models['Generator']}...")
            AutoTokenizer.from_pretrained(self.models['Generator'])
            AutoModelForCausalLM.from_pretrained(
                self.models['Generator'],
                load_in_4bit=True,
                torch_dtype=torch.bfloat16
            )
            self.progress.emit("Generator model check: OK")
        except Exception as e:
            self.finished.emit(f"Failed to load Generator model: {e}", False)
            return

        self.finished.emit("All AI models loaded successfully!", True)
