import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from .hybrid_retriever import HybridRetriever
from .document_classifier import DocumentClassifier, DocumentType
from .parsing import parse_document_into_sections
from typing import Dict, List
import json

class ComplianceAnalyzer:
    def __init__(self):
	@@ -24,66 +24,86 @@ def __init__(self):
        generator_model_name = "nabilfaieaz/tinyllama-med-full"

        self.generator_tokenizer = AutoTokenizer.from_pretrained(generator_model_name)
        quantization_config = BitsAndBytesConfig(load_in_4bit=True)
        self.generator_model = AutoModelForCausalLM.from_pretrained(
            generator_model_name,
            quantization_config=quantization_config,
            dtype=torch.bfloat16, # Use bfloat16 for better performance on modern GPUs
            device_map="auto"
        )
        print(f"Generator LLM '{generator_model_name}' loaded successfully.")

        print("\nCompliance Analyzer initialized successfully.")

    def analyze_document(self, document_text: str) -> Dict:
        """
        Analyzes a document for compliance.
        :param document_text: The full text of the document to analyze.
        :return: A dictionary containing the compliance analysis.
        """
        print("\n--- Starting Compliance Analysis ---")
        print(f"Analyzing document: '{document_text[:100]}...'")

        # 1. Extract entities
        entities = self.ner_pipeline(document_text)
        entity_list = ", ".join([f"'{entity['word']}' ({entity['entity_group']})" for entity in entities])

        # 2. Retrieve context
        retrieved_docs = self.retriever.search(document_text)
        context = "\n".join(retrieved_docs)
        # Truncate context to avoid exceeding model's context window
        max_context_length = 4000
        if len(context) > max_context_length:
            context = context[:max_context_length] + "\n..."


        # 3. Build prompt
        prompt = self._build_prompt(document_text, entity_list, context)

        # 4. Generate with LLM
        inputs = self.generator_tokenizer(prompt, return_tensors="pt").to(self.generator_model.device)
        output = self.generator_model.generate(**inputs, max_new_tokens=512, num_return_sequences=1)
        result = self.generator_tokenizer.decode(output[0], skip_special_tokens=True)

        # 5. Extract and parse JSON
        try:
            # The model sometimes includes the prompt in the output, so we find the start of the JSON.
            json_start = result.find('```json')
            if json_start != -1:
                json_str = result[json_start + 7:].strip()
                # And the end of the JSON
                json_end = json_str.rfind('```')
                if json_end != -1:
                    json_str = json_str[:json_end].strip()
            else:
                # Fallback if the ```json``` markers are not present
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                json_str = result[json_start:json_end]

            analysis = json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            print(f"Error parsing JSON output: {e}")
            print(f"Raw model output:\n{result}")
            analysis = {"error": "Failed to parse JSON output from model."}

        print("Analysis generated.")
        return analysis

    def _build_prompt(self, document: str, entity_list: str, context: str) -> str:
        """
        Builds the prompt for the LLM.
        """
        return f"""
You are an expert Medicare compliance officer for a Skilled Nursing Facility (SNF). Your task is to analyze a clinical therapy document for potential compliance risks based on the provided Medicare guidelines.
**Clinical Document:**
---
{document}
---
**Extracted Clinical Entities:**
---
{entity_list}
---
	@@ -92,35 +112,30 @@ def _build_section_prompt(self, section_name, section_text, entities, context, d
---
{context}
---
**Your Task:**
Based on all the information above, provide a detailed compliance analysis. Identify any potential risks, explain why they are risks according to the guidelines, and suggest specific actions to mitigate them. If no risks are found, state that the document appears to be compliant.
**Output Format:**
Return the analysis as a JSON object with the following structure:
{{
  "findings": [
    {{
      "text": "<text from the original document that contains the finding>",
      "risk": "<description of the compliance risk>",
      "suggestion": "<suggestion to mitigate the risk>"
    }}
  ]
}}
**Compliance Analysis:**
```json
"""

if __name__ == '__main__':
    analyzer = ComplianceAnalyzer()

    # Sample clinical document
    sample_document = '''
Subjective: Patient reports feeling tired but motivated. States goal is to "walk my daughter down the aisle."
Objective: Patient participated in 45 minutes of physical therapy. Gait training on level surfaces with rolling walker for 100 feet with moderate assistance. Moderate verbal cueing required for sequencing.
	@@ -131,6 +146,4 @@ def _build_section_prompt(self, section_name, section_text, entities, context, d
    analysis_results = analyzer.analyze_document(sample_document)

    print("\n\n--- FINAL COMPLIANCE ANALYSIS ---")
    print(json.dumps(analysis_results, indent=2))
