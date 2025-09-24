from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import torch

class NERPipeline:
    def __init__(self, model_name: str, quantization: str = "none", performance_profile: str = "medium"):

        if performance_profile == "low":
            torch_dtype = torch.float16
        elif performance_profile == "medium":
            torch_dtype = torch.bfloat16
        else:
            torch_dtype = torch.float32

        tokenizer = AutoTokenizer.from_pretrained(model_name)

        if quantization == "8bit":
            model = AutoModelForTokenClassification.from_pretrained(model_name, load_in_8bit=True, torch_dtype=torch_dtype)
        elif quantization == "4bit":
            model = AutoModelForTokenClassification.from_pretrained(model_name, load_in_4bit=True, torch_dtype=torch_dtype)
        else:
            model = AutoModelForTokenClassification.from_pretrained(model_name, torch_dtype=torch_dtype)

        self.pipeline = pipeline("ner", model=model, tokenizer=tokenizer)

    def extract_entities(self, text: str):
        return self.pipeline(text)