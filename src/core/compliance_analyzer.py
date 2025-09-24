import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from .hybrid_retriever import HybridRetriever
from document_classifier import DocumentClassifier, DocumentType
from parsing import parse_document_into_sections
from typing import Dict, List
import json
from rubric_service import ComplianceRule

class ComplianceAnalyzer:
    def __init__(self):
        # Initialize the NER pipeline
        ner_model_name = "samrawal/bert-base-uncased_clinical-ner"
        self.ner_pipeline = pipeline("ner", model=ner_model_name, grouped_entities=True)
        print(f"NER model '{ner_model_name}' loaded successfully.")

        # Initialize the document classifier
        self.classifier = DocumentClassifier()
        print("Document Classifier initialized successfully.")

        # Initialize the GraphRAG retriever
        self.retriever = HybridRetriever()
        print("GraphRAG Hybrid Retriever initialized successfully.")

        # Initialize the generator LLM
        generator_model_name = "nabilfaieaz/tinyllama-med-full"
        self.generator_tokenizer = AutoTokenizer.from_pretrained(generator_model_name)
        quantization_config = BitsAndBytesConfig(load_in_4bit=True)
        self.generator_model = AutoModelForCausalLM.from_pretrained(
            generator_model_name,
            quantization_config=quantization_config,
            dtype=torch.bfloat16,
            device_map="auto"
        )
        print(f"Generator LLM '{generator_model_name}' loaded successfully.")
        print("\nCompliance Analyzer initialized successfully.")

    def analyze_document(self, document_text: str, discipline: str) -> Dict:
        """
        Analyzes a document for compliance.
        :param document_text: The full text of the document to analyze.
        :param discipline: The discipline to filter by (e.g., 'pt', 'ot', 'slp').
        :return: A dictionary containing the compliance analysis.
        """
        print("\n--- Starting Compliance Analysis ---")
        print(f"Analyzing document: '{document_text[:100]}...'")

        # 1. Classify document type
        doc_type = self.classifier.classify(document_text)
        doc_type_str = doc_type.value if doc_type else "Unknown"
        print(f"Document classified as: {doc_type_str}")

        # 2. Extract entities
        entities = self.ner_pipeline(document_text)
        entity_list = ", ".join([f"'{entity['word']}' ({entity['entity_group']})" for entity in entities])
        print(f"Extracted entities: {entity_list}")

        # 3. Retrieve context from GraphRAG
        retrieved_rules = self.retriever.search(document_text, discipline=discipline, doc_type=doc_type_str)
        context = self._format_rules_for_prompt(retrieved_rules)

        # Truncate context to avoid exceeding model's context window
        max_context_length = 4000
        if len(context) > max_context_length:
            context = context[:max_context_length] + "\n..."
        print("Retrieved and formatted context from GraphRAG.")

        # 4. Build prompt
        prompt = self._build_prompt(document_text, entity_list, context)

        # 5. Generate with LLM
        inputs = self.generator_tokenizer(prompt, return_tensors="pt").to(self.generator_model.device)
        output = self.generator_model.generate(**inputs, max_new_tokens=512, num_return_sequences=1)
        result = self.generator_tokenizer.decode(output[0], skip_special_tokens=True)

        # 6. Extract and parse JSON
        try:
            json_start = result.find('```json')
            if json_start != -1:
                json_str = result[json_start + 7:].strip()
                json_end = json_str.rfind('```')
                if json_end != -1:
                    json_str = json_str[:json_end].strip()
            else:
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

    def _format_rules_for_prompt(self, rules: List[ComplianceRule]) -> str:
        """
        Formats a list of ComplianceRule objects into a string for the prompt.
        """
        if not rules:
            return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."

        formatted_rules = []
        for rule in rules:
            formatted_rules.append(
                f"- **Rule:** {rule.issue_title}\n"
                f"  **Detail:** {rule.issue_detail}\n"
                f"  **Suggestion:** {rule.suggestion}"
            )
        return "\n".join(formatted_rules)

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

**Relevant Medicare Compliance Rules:**
---
{context}
---

**Your Task:**
Based on all the information above, provide a detailed compliance analysis. Identify any potential risks, explain why they are risks according to the retrieved rules, and suggest specific actions to mitigate them. If no risks are found, state that the document appears to be compliant.

**Output Format:**
Return the analysis as a JSON object with the following structure:
{{
  "findings": [
    {{
      "text": "<text from the original document that contains the finding>",
      "risk": "<description of the compliance risk based on the retrieved rules>",
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
Assessment: Patient making slow but steady progress towards goals. Would benefit from continued skilled therapy to improve safety and independence with ambulation.
Plan: Continue PT 5x/week for 2 weeks to address gait, balance, and functional mobility.
'''
    # Analyze the document for a specific discipline
    analysis_results = analyzer.analyze_document(sample_document, discipline="pt")

    print("\n\n--- FINAL COMPLIANCE ANALYSIS ---")
    print(json.dumps(analysis_results, indent=2))
