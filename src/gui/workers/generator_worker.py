import torch
from PyQt6.QtCore import QObject, pyqtSignal
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from typing import List

class GeneratorWorker(QObject):
    """
    A worker for generating text answers using a causal language model,
    based on a provided question and context (RAG pattern).
    """
    finished = pyqtSignal(str)  # Emits the generated answer string
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)

    def __init__(self, question: str, context: List[str]):
        super().__init__()
        self.question = question
        self.context_str = "\n---\n".join(context)
        self._cancel = False
        self.generator_pipeline = None
        self.model_name = "nabilfaieaz/tinyllama-med-full"

    def cancel(self):
        """Requests cancellation of the generation process."""
        self._cancel = True

    def _load_model(self):
        """Loads the quantized generator model and its tokenizer."""
        self.progress.emit(10, f"Loading generator model '{self.model_name}'...")
        try:
            # Load the tokenizer
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            # Load the model with 4-bit quantization for efficiency
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                load_in_4bit=True,
                device_map="auto",
                torch_dtype=torch.bfloat16  # Recommended for faster inference
            )

            self.generator_pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                torch_dtype=torch.bfloat16,
                device_map="auto"
            )
            self.progress.emit(25, "Generator model loaded successfully.")
            return True
        except Exception as e:
            self.error.emit(f"Failed to load generator model: {e}")
            return False

    def _build_prompt(self) -> str:
        """Builds a clear and structured prompt for the language model."""
        # This prompt structure is designed to minimize hallucinations
        # and force the model to rely on the provided context.
        return (
            "You are an expert assistant. Use the following context to answer the question. "
            "If the answer is not found in the context, state that clearly. "
            "Do not add any information that is not in the context.\n\n"
            "--- CONTEXT ---\n"
            f"{self.context_str}\n\n"
            "--- QUESTION ---\n"
            f"{self.question}\n\n"
            "--- ANSWER ---\n"
        )

    def run(self):
        """
        Loads the model, generates text based on the prompt, and emits the result.
        """
        if not self._load_model():
            return

        if self._cancel or not self.generator_pipeline:
            self.error.emit("Generator operation canceled before starting.")
            return

        prompt = self._build_prompt()
        self.progress.emit(50, "Generating answer...")

        try:
            # Generate the text sequence
            sequences = self.generator_pipeline(
                prompt,
                max_new_tokens=300,  # Limit the answer length
                do_sample=True,
                top_k=10,
                num_return_sequences=1,
                eos_token_id=self.generator_pipeline.tokenizer.eos_token_id,
            )

            if self._cancel:
                self.error.emit("Generator operation canceled during generation.")
                return

            # Clean the output to get only the answer text
            full_text = sequences[0]['generated_text']
            # The answer is what comes after the "--- ANSWER ---" marker in our prompt.
            answer = full_text.split("--- ANSWER ---")[1].strip()

            self.progress.emit(100, "Generation complete.")
            self.finished.emit(answer)

        except Exception as e:
            self.error.emit(f"An error occurred during text generation: {e}")
