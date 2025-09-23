import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from hybrid_retriever import HybridRetriever
from src.document_classifier import DocumentClassifier, DocumentType
from src.parsing import parse_text_into_sections, parse_document_into_sections
from typing import Dict, List

class ComplianceAnalyzer:
    def __init__(self):
        print("Initializing Compliance Analyzer...")

        # 1. Initialize the Hybrid Retriever
        self.retriever = HybridRetriever()

        # 2. Load the NER Model
        print("Loading NER model...")
        ner_model_name = "OpenMed/OpenMed-NER-PathologyDetect-PubMed-v2-109M"
        self.ner_pipeline = pipeline("token-classification", model=ner_model_name, aggregation_strategy="simple")
        print(f"NER model '{ner_model_name}' loaded successfully.")

        # 3. Load the Generator LLM (TinyLlama)
        print("\nLoading Generator LLM (TinyLlama)...")
        generator_model_name = "nabilfaieaz/tinyllama-med-full"

        self.generator_tokenizer = AutoTokenizer.from_pretrained(generator_model_name)
        self.generator_model = AutoModelForCausalLM.from_pretrained(
            generator_model_name,
            load_in_4bit=True,
            torch_dtype=torch.bfloat16, # Use bfloat16 for better performance on modern GPUs
            device_map="auto"
        )
        print(f"Generator LLM '{generator_model_name}' loaded successfully.")

        print("\nCompliance Analyzer initialized successfully.")

    def analyze_document(self, document_text: str) -> Dict[str, str]:
        """
        Analyzes a document for compliance, performing a section-by-section analysis.

        :param document_text: The full text of the document to analyze.
        :return: A dictionary with section names as keys and their compliance analysis as values.
        """
        print("\n--- Starting Compliance Analysis ---")
        print(f"Analyzing document: '{document_text[:100]}...'")

def analyze_document(self, document_text: str) -> Dict[str, str]:
    """
    Analyzes a document for compliance, performing a section-by-section analysis.
    Returns a dictionary with section names as keys and their compliance analysis as values.
    """
    print("\n--- Starting Compliance Analysis ---")
    print(f"Analyzing document: '{document_text[:100]}...'")

    # Step 1: Parse the document into sections (hybrid logic)
    print("\nStep 1: Parsing document into sections...")
    sections = parse_text_into_sections(document_text)
    print(f"Found sections: {list(sections.keys())}")

    # Step 2: Extract entities with NER
    print("\nStep 2: Extracting entities with NER...")
    entities = self.ner_pipeline(document_text)
    print(f"Found entities: {[entity['word'] for entity in entities]}")

    # Step 3: Retrieve relevant guidelines
    print("\nStep 3: Retrieving relevant guidelines with Hybrid Retriever...")
    query = document_text
    retrieved_docs = self.retriever.search(query, top_k=3)
    context = "\n\n".join(retrieved_docs)
    print("Retrieved context successfully.")

    # Step 4: Classify document type and load relevant rubric
    classifier = DocumentClassifier()
    doc_type = classifier.classify(document_text)
    rubric = self._load_rubric(doc_type)

    # Step 5: Advanced section-by-section analysis
    analysis_results = {}
    for section_name, section_text in sections.items():
        analysis = self._analyze_section(
            section_name, section_text, entities, context, doc_type, rubric
        )
        analysis_results[section_name] = analysis

    print("\nCompliance analysis generated successfully for all sections.")
    return analysis_results

def _analyze_section(self, section_name: str, section_text: str, entities: List[Dict], context: str, doc_type: DocumentType, rubric: str) -> str:
    """Analyzes a single section of the document."""
    print(f"\n--- Analyzing Section: {section_name} ---")
    prompt = self._build_section_prompt(section_name, section_text, entities, context, doc_type, rubric)
    inputs = self.generator_tokenizer(prompt, return_tensors="pt").to(self.generator_model.device)
    output = self.generator_model.generate(**inputs, max_new_tokens=256, num_return_sequences=1)
    result = self.generator_tokenizer.decode(output[0], skip_special_tokens=True)
    analysis_part = result.split("Section Compliance Analysis:")[-1].strip()
    print(f"Analysis generated for section: {section_name}")
    return analysis_part

def _load_rubric(self, doc_type: DocumentType | None) -> str | None:
    """Loads the rubric file based on the document type."""
    if not doc_type:
        return None
    rubric_path = f"resources/rubrics/{doc_type.name.lower()}_rubric.txt"
    try:
        with open(rubric_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return None

def _build_section_prompt(self, section_name, section_text, entities, context, doc_type, rubric):
    """Helper function to build the detailed prompt for analyzing a single section."""
    entity_list = ", ".join([f"'{entity['word']}' ({entity['entity_group']})" for entity in entities])
    doc_type_str = doc_type.value if doc_type else "Unknown"
    prompt = f"""
You are an expert Medicare compliance officer for a Skilled Nursing Facility (SNF). Your task is to analyze a specific section of a clinical therapy document for potential compliance risks.
**Document Type:** {doc_type_str}
**Section to Analyze:** {section_name}
**Full list of Extracted Clinical Entities from Document:**
---
{entity_list}
---
**Relevant Medicare Guidelines (from Chapter 8: Coverage of Extended Care (SNF) Services):**
---
{context}
---
"""
    if rubric:
        prompt += f"""
**Compliance Rubric for {doc_type_str}:**
---
{rubric}
---
"""
    prompt += f"""
**Content of the '{section_name}' section:**
---
{section_text}
---
**Your Task:**
Based on all the information above, provide a detailed compliance analysis FOR THE '{section_name}' SECTION ONLY. Identify any potential risks within this section, explain why they are risks according to the guidelines and the provided rubric, and suggest specific actions to mitigate them. If no risks are found for this section, state that the section appears to be compliant.
**Section Compliance Analysis:**
"""
    return prompt
