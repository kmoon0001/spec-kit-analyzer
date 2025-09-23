import torch
import logging
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from hybrid_retriever import HybridRetriever

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ComplianceAnalyzer:
    def __init__(self):
        logging.info("Initializing Compliance Analyzer...")

        # 1. Initialize the Hybrid Retriever
        self.retriever = HybridRetriever()

        # 2. Load the NER Model
        logging.info("Loading NER model...")
        ner_model_name = "OpenMed/OpenMed-NER-PathologyDetect-PubMed-v2-109M"
        self.ner_pipeline = pipeline("token-classification", model=ner_model_name, revision="e00c20f", aggregation_strategy="simple")
        logging.info(f"NER model '{ner_model_name}' loaded successfully.")

        # 3. Load the Generator LLM (TinyLlama)
        logging.info("\nLoading Generator LLM (TinyLlama)...")
        generator_model_name = "nabilfaieaz/tinyllama-med-full"

        self.generator_tokenizer = AutoTokenizer.from_pretrained(generator_model_name, revision="f9e026b")
        self.generator_model = AutoModelForCausalLM.from_pretrained(
            generator_model_name,
            revision="f9e026b",
            load_in_4bit=True,
            torch_dtype=torch.bfloat16, # Use bfloat16 for better performance on modern GPUs
            device_map="auto"
        )
        logging.info(f"Generator LLM '{generator_model_name}' loaded successfully.")

        logging.info("\nCompliance Analyzer initialized successfully.")

    def analyze_document(self, document_text):
        logging.info("\n--- Starting Compliance Analysis ---")
        logging.info(f"Analyzing document: '{document_text[:100]}...'")

        # Step 1: Extract entities using the NER model
        logging.info("\nStep 1: Extracting entities with NER...")
        entities = self.ner_pipeline(document_text)
        logging.info(f"Found entities: {[entity['word'] for entity in entities]}")

        # Create a query for the retriever based on the document text and entities
        query = document_text

        # Step 2: Retrieve relevant guidelines using the Hybrid Retriever
        logging.info("\nStep 2: Retrieving relevant guidelines with Hybrid Retriever...")
        retrieved_docs = self.retriever.search(query, top_k=3) # Get top 3 most relevant sections

        context = "\n\n".join(retrieved_docs)
        logging.info("Retrieved context successfully.")

        # Step 3: Construct the prompt for the LLM
        logging.info("\nStep 3: Constructing prompt for LLM...")
        prompt = self._build_prompt(document_text, entities, context)

        # Step 4: Generate compliance analysis using the LLM
        logging.info("\nStep 4: Generating compliance analysis with LLM...")

        inputs = self.generator_tokenizer(prompt, return_tensors="pt").to(self.generator_model.device)

        # Generate the output
        output = self.generator_model.generate(**inputs, max_new_tokens=512, num_return_sequences=1)

        # Decode and return the result
        result = self.generator_tokenizer.decode(output[0], skip_special_tokens=True)

        # Clean up the output to only return the analysis part
        analysis_part = result.split("Compliance Analysis:")[-1].strip()

        logging.info("Compliance analysis generated successfully.")
        return analysis_part

    def _build_prompt(self, document, entities, context):
        """Helper function to build the detailed prompt for the LLM."""

        entity_list = ", ".join([f"'{entity['word']}' ({entity['entity_group']})" for entity in entities])

        prompt = f"""
You are an expert Medicare compliance officer for a Skilled Nursing Facility (SNF). Your task is to analyze a clinical therapy document for potential compliance risks based on the provided Medicare guidelines.

**Clinical Document:**
---
{document}
---

**Extracted Clinical Entities:**
---
{entity_list}
---

**Relevant Medicare Guidelines (from Chapter 8: Coverage of Extended Care (SNF) Services):**
---
{context}
---

**Your Task:**
Based on all the information above, provide a detailed compliance analysis. Identify any potential risks, explain why they are risks according to the guidelines, and suggest specific actions to mitigate them. If no risks are found, state that the document appears to be compliant.

**Compliance Analysis:**
"""
        return prompt

if __name__ == '__main__':
    analyzer = ComplianceAnalyzer()

    # Sample clinical document with a potential compliance issue
    # (The issue: therapy might not be seen as "daily" if it's only 3 times a week without justification)
    sample_document = "Patient with post-stroke hemiparesis is receiving physical therapy 3 times per week to improve gait and balance. The goal is to increase independence with ambulation. The patient is motivated and shows slow but steady progress. The SNF stay is covered under Medicare Part A."

    analysis = analyzer.analyze_document(sample_document)

    print("\n\n--- FINAL COMPLIANCE ANALYSIS ---")
    print(analysis)
