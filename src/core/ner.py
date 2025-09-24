from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

class NERPipeline:
    def __init__(self, model_name: str):
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForTokenClassification.from_pretrained(model_name)
        self.pipeline = pipeline("ner", model=model, tokenizer=tokenizer)

    def extract_entities(self, text: str):
        return self.pipeline(text)