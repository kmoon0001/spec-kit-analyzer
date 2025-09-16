# src/nlg_service.py
import logging
from transformers import T5ForConditionalGeneration, T5Tokenizer

logger = logging.getLogger(__name__)

class NLGService:
    def __init__(self, model_name="t5-small"):
        """
        Initializes the NLG service with a pre-trained T5 model.
        """
        try:
            self.model = T5ForConditionalGeneration.from_pretrained(model_name)
            self.tokenizer = T5Tokenizer.from_pretrained(model_name)
            logger.info(f"NLG model '{model_name}' loaded successfully.")
        except Exception as e:
            self.model = None
            self.tokenizer = None
            logger.error(f"Failed to load NLG model '{model_name}': {e}")

    def generate_tip(self, prompt: str) -> str:
        """
        Generates a personalized tip based on the given prompt.
        """
        if not self.model or not self.tokenizer:
            return "NLG service is not available."

        try:
            input_text = f"generate a helpful tip: {prompt}"
            input_ids = self.tokenizer.encode(input_text, return_tensors="pt")

            # Generate the output
            output_ids = self.model.generate(
                input_ids,
                max_length=150,
                num_beams=4,
                early_stopping=True,
                no_repeat_ngram_size=2,
            )

            # Decode the output
            tip = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
            return tip
        except Exception as e:
            logger.error(f"Failed to generate tip: {e}")
            return "Failed to generate tip."
