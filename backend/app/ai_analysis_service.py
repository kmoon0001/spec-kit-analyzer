import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List, Dict

class AIAnalysisService:
    """
    A dedicated service for handling interactions with the Language Model.
    """
    _model = None
    _tokenizer = None

    def __init__(self): 
        """
        Initializes the service and loads the language model.
        This uses a singleton pattern to ensure the model is loaded only once.
        """
        if AIAnalysisService._model is None:
            print("Initializing AI Analysis Service and loading model...")
            model_name = "nabilfaieaz/tinyllama-med-full"
            try:
                AIAnalysisService._tokenizer = AutoTokenizer.from_pretrained(model_name)
                AIAnalysisService._model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    load_in_4bit=True,
                    torch_dtype=torch.bfloat16,
                    device_map="auto"
                )
                print(f"AI model '{model_name}' loaded successfully.")
            except Exception as e:
                print(f"Fatal error loading AI model: {e}")
                # If the model fails to load, the service will be non-functional.
                AIAnalysisService._model = None
                AIAnalysisService._tokenizer = None

    def generate_enhanced_analysis(self, doc_type: str, findings: List[Dict], guidelines: List[Dict]) -> str:
        """
        Generates an enhanced, narrative analysis for a document.
        This is where the "Context Engineering" happens.

        Args:
            doc_type (str): The type of the document (e.g., "Evaluation").
            findings (List[Dict]): A list of rule-based findings.
            guidelines (List[Dict]): A list of relevant guideline snippets.

        Returns:
            str: The AI-generated narrative summary.
        """
        if not self._model or not self._tokenizer:
            return "The AI Analysis model is not available."

        prompt = self._build_prompt(doc_type, findings, guidelines)

        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)

        output = self._model.generate(**inputs, max_new_tokens=400, num_return_sequences=1, temperature=0.7, top_p=0.9)

        result = self._tokenizer.decode(output[0], skip_special_tokens=True)

        # Clean up the output to only return the analysis part
        analysis = result.split("Analysis:")[-1].strip()

        return analysis

    def _build_prompt(self, doc_type: str, findings: List[Dict], guidelines: List[Dict]) -> str:
        """
        This is the "Context Engine". It builds a rich, context-aware prompt for the LLM.
        """

        # --- 1. Build sections for findings and guidelines ---
        findings_text = ""
        if not findings:
            findings_text = "No specific compliance risks were found based on the keyword rubric."
        else:
            for i, finding in enumerate(findings, 1):
                findings_text += f"{i}. {finding.get('issue_title', 'N/A')} (Severity: {finding.get('severity', 'N/A')})\n"
                findings_text += f"   - Details: {finding.get('issue_detail', 'N/A')}\n"

        guidelines_text = ""
        if not guidelines:
            guidelines_text = "No relevant guidelines were retrieved for the identified findings."
        else:
            for i, group in enumerate(guidelines, 1):
                guidelines_text += f"Guideline related to '{group.get('related_to', 'N/A')}':\n"
                for guideline in group.get('guidelines', []):
                    guidelines_text += f"   - Source: {guideline.get('source', 'N/A')}\n"
                    guidelines_text += f"   - Text: \"{guideline.get('text', '')}\"\n"

        # --- 2. Select a prompt template based on document type ---

        # Base prompt for all types
        base_prompt = """
You are an expert Medicare compliance consultant. Your task is to provide a holistic, narrative analysis based on a set of pre-identified findings and relevant guidelines. Your analysis should be professional, objective, and tailored to the type of clinical document.
"""

        # Type-specific instructions
        if doc_type == "Evaluation / Recertification":
            type_instructions = "Focus on whether the findings suggest a failure to establish a comprehensive baseline, a clear plan of care, or justify the medical necessity for the episode of care. Synthesize the findings into a coherent summary of the evaluation's overall compliance."
        elif doc_type == "Progress Report":
            type_instructions = "Focus on whether the findings suggest a failure to document progress towards goals, justify continued treatment, or modify the plan of care as needed. Synthesize the findings into a coherent summary of the progress note's compliance."
        elif doc_type == "Discharge Summary":
            type_instructions = "Focus on whether the findings suggest a failure to adequately summarize the course of treatment, patient status at discharge, or provide clear recommendations for follow-up. Synthesize the findings into a coherent summary of the discharge note's compliance."
        else: # Daily Note or Unknown
            type_instructions = "Focus on whether the findings suggest a failure to document skilled, medically necessary services for the date of service. Synthesize the findings into a brief summary of the daily note's compliance."

        # --- 3. Assemble the final prompt ---
        full_prompt = f"""
{base_prompt}

**Instructions for this Analysis:**
{type_instructions}

**Rule-Based Findings:**
---
{findings_text}
---

**Relevant Medicare Guideline Excerpts:**
---
{guidelines_text}
---

**Your Task:**
Based *only* on the information provided above, write a short, narrative compliance analysis. Do not repeat the findings verbatim, but rather summarize the key compliance risks and their implications.

**Analysis:**
"""
        return full_prompt
