import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from hybrid_retriever import HybridRetriever
from src.parsing import parse_text_into_sections

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

    def analyze_document(self, document_text):
        print("\n--- Starting Compliance Analysis ---")
        print(f"Analyzing document: '{document_text[:100]}...'")

        # Step 1: Parse the document into sections
        print("\nStep 1: Parsing document into sections...")
        sections = parse_text_into_sections(document_text)
        print(f"Found sections: {list(sections.keys())}")

        # Step 2: Extract entities using the NER model
        print("\nStep 2: Extracting entities with NER...")
        entities = self.ner_pipeline(document_text)
        print(f"Found entities: {[entity['word'] for entity in entities]}")

        # Create a query for the retriever based on the document text and entities
        query = document_text

        # Step 3: Retrieve relevant guidelines using the Hybrid Retriever
        print("\nStep 3: Retrieving relevant guidelines with Hybrid Retriever...")
        retrieved_docs = self.retriever.search(query, top_k=3)

        context = "\n\n".join(retrieved_docs)
        print("Retrieved context successfully.")

        # Step 4: Construct the prompt for the LLM
        print("\nStep 4: Constructing prompt for LLM...")
        prompt = self._build_prompt(sections, entities, context)

        # Step 5: Generate compliance analysis using the LLM
        print("\nStep 4: Generating compliance analysis with LLM...")

        inputs = self.generator_tokenizer(prompt, return_tensors="pt").to(self.generator_model.device)

        # Generate the output
        output = self.generator_model.generate(**inputs, max_new_tokens=512, num_return_sequences=1)

        # Decode and return the result
        result = self.generator_tokenizer.decode(output[0], skip_special_tokens=True)

        # Clean up the output to only return the analysis part
        analysis_part = result.split("Compliance Analysis:")[-1].strip()

        print("Compliance analysis generated successfully.")
        return {
            "analysis": analysis_part,
            "sources": retrieved_docs
        }

    def _build_prompt(self, sections, entities, context):
        """Helper function to build the detailed prompt for the LLM."""

        entity_list = ", ".join([f"'{entity['word']}' ({entity['entity_group']})" for entity in entities])

        # Format the sections for the prompt
        document_details = "\n".join([f"**{header}:**\n{content}" for header, content in sections.items()])

        prompt = f"""
You are an expert Medicare compliance officer for a Skilled Nursing Facility (SNF). Your task is to analyze a clinical therapy document for potential compliance risks based on the provided Medicare guidelines.

**Clinical Document Sections:**
---
{document_details}
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

    # Sample clinical document with sections and a potential compliance issue
    sample_document = """
    Subjective: Patient reports feeling tired but motivated.
    Objective: Patient participated in 30 minutes of physical therapy, 3 times this week. Focused on gait and balance exercises. Vital signs stable.
    Assessment: Slow but steady progress noted in ambulation. Still requires supervision.
    Plan: Continue with current therapy regimen. Re-evaluate in 1 week. The SNF stay is covered under Medicare Part A.
    """

    result = analyzer.analyze_document(sample_document)

    print("\n\n--- FINAL COMPLIANCE ANALYSIS ---")
    print(result["analysis"])
    print("\n--- SOURCES ---")
    for source in result["sources"]:
        print(f"- {source}")
