import logging
import torch
import json
import re
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from src.guideline_service import GuidelineService
from src.rubric_service import ComplianceRule
from src.utils import load_config

logger = logging.getLogger(__name__)

# ========== Prompt Template Manager ==========
class PromptManager:
    def __init__(self, config):
        # Load prompt templates from config or external file
        self.template = config.get('prompt_template', self.default_template())

    def default_template(self):
        return (
            "You are an expert Medicare compliance officer for a Skilled Nursing Facility (SNF). "
            "Your task is to analyze a clinical therapy document for potential compliance risks based on the provided Medicare guidelines.\n\n"
            "**Clinical Document:**\n---\n{document}\n---\n\n"
            "**Extracted Clinical Entities:**\n---\n{entities}\n---\n"
            "**Relevant Medicare Guidelines:**\n---\n{context}\n---\n"
            "**Your Task:**\nBased on all the information above, provide a detailed compliance analysis. "
            "Identify any potential risks, explain why they are risks according to the retrieved rules, and suggest specific actions to mitigate them. "
            "If no risks are found, state that the document appears to be compliant.\n\n"
            "**Output Format:**\nReturn the analysis as a JSON object.\n\n"
            "**Compliance Analysis:**\n"
        )

    def build_prompt(self, document, entities, context):
        return self.template.format(document=document, entities=entities, context=context)

# ========== NER Entity Extractor ==========
class EntityExtractor:
    def __init__(self, config):
        ner_model = config.get("ner_model", None)
        self.ner_pipeline = pipeline("ner", model=ner_model) if ner_model else None

    def extract(self, text):
        if self.ner_pipeline:
            entities = self.ner_pipeline(text)
            return ", ".join([f"'{e['word']}' ({e['entity_group']})" for e in entities])
        else:
            return ""

# ========== Explanation Engine ==========
class ExplanationEngine:
    def __init__(self, config):
        # Customize as needed for model/logic
        pass

    def generate_explanation(self, analysis):
        # Example: add rationale for each finding (expand with custom logic)
        if 'findings' in analysis:
            for finding in analysis['findings']:
                finding['explanation'] = f"Risk was identified due to presence of: {finding.get('risk', 'N/A')}"
        return analysis

# ========== Main ComplianceAnalyzer Pipeline ==========
class ComplianceAnalyzer:
    """
    Flexible clinical document compliance analyzer. Modular, config-driven, extensible.
    Supports retriever/RAG, guideline system, quantized LLM, prompt manager, NER, explanation post-process.
    """
    def __init__(
        self,
        guideline_service: GuidelineService = None,
        retriever=None,
        config=None,
        use_query_transformation=False
    ):
        self.config = config or load_config()
        generator_model_name = self.config['models'].get('generator', "nabilfaieaz/tinyllama-med-full")

        logger.info(f"Initializing ComplianceAnalyzer with model: {generator_model_name}")

        self.guideline_service = guideline_service or GuidelineService()
        self.retriever = retriever if retriever else None

        quantization = self.config.get('quantization', {})
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=quantization.get('load_in_4bit', True),
            bnb_4bit_quant_type=quantization.get('quant_type', "nf4"),
            bnb_4bit_compute_dtype=getattr(torch, quantization.get('compute_dtype', "bfloat16")),
        )

        self.generator_tokenizer = AutoTokenizer.from_pretrained(generator_model_name)
        self.generator_model = AutoModelForCausalLM.from_pretrained(
            generator_model_name,
            quantization_config=quantization_config,
            device_map="auto"
        )
        logger.info(f"Generator LLM '{generator_model_name}' loaded successfully.")

        self.use_query_transformation = use_query_transformation

        # Modular helpers
        self.prompt_manager = PromptManager(self.config)
        self.entity_extractor = EntityExtractor(self.config)
        self.explanation_engine = ExplanationEngine(self.config)

    def analyze_document(self, document_text: str, discipline: str, analysis_mode: str = "llm_only") -> dict:
        logger.info("--- Starting Compliance Analysis ---")
        logger.info(f"Analyzing document: '{document_text[:100]}...'")

        entities_str = self.entity_extractor.extract(document_text)
        logger.info(f"Extracted entities: {entities_str}")

        doc_type = self.guideline_service.classify_document(document_text)
        doc_type_str = doc_type.value if hasattr(doc_type, 'value') else str(doc_type)
        logger.info(f"Classified as: {doc_type_str}")

        query = document_text
        doc_type_obj = doc_type
        if self.use_query_transformation:
            query = self._transform_query(query)
        retrieved_rules = (
            self.retriever.search(query=query, discipline=discipline, doc_type=doc_type_obj.name)
            if self.retriever else
            self.guideline_service.search(query=query, discipline=discipline, doc_type=doc_type_obj.name)
        )
        context_str = self._format_rules_for_prompt(retrieved_rules)
        logger.info("Retrieved and formatted context.")

        prompt = self.prompt_manager.build_prompt(document_text, entities_str, context_str)

        inputs = self.generator_tokenizer(prompt, return_tensors="pt").to(self.generator_model.device)
        output = self.generator_model.generate(**inputs, max_new_tokens=512, num_return_sequences=1)
        result = self.generator_tokenizer.decode(output[0], skip_special_tokens=True)

        analysis = self._parse_json_output(result)
        logger.info("Raw model analysis returned.")

        while "search" in analysis:
            search_query = analysis["search"]
            logger.info(f"LLM requested a search: {search_query}")
            retrieved_rules = self.guideline_service.search(query=search_query)
            context_str = self._format_rules_for_prompt(retrieved_rules)
            prompt = self.prompt_manager.build_prompt(document_text, entities_str, context_str)
            inputs = self.generator_tokenizer(prompt, return_tensors="pt").to(self.generator_model.device)
            output = self.generator_model.generate(**inputs, max_new_tokens=512, num_return_sequences=1)
            result = self.generator_tokenizer.decode(output[0], skip_special_tokens=True)
            analysis = self._parse_json_output(result)

        analysis = self.explanation_engine.generate_explanation(analysis)
        logger.info("Explanations generated.")

        return analysis

    def _transform_query(self, query: str) -> str:
        return query

    def _format_rules_for_prompt(self, rules: list) -> str:
        if not rules:
            return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."
        formatted_rules = []
        for rule in rules:
            formatted_rules.append(
                f"- **Rule:** {getattr(rule, 'issue_title', '')}\n"
                f"  **Detail:** {getattr(rule, 'issue_detail', '')}\n"
                f"  **Suggestion:** {getattr(rule, 'suggestion', '')}"
            )
        return "\n".join(formatted_rules)

    def _parse_json_output(self, result: str) -> dict:
        try:
            # Correctly handle JSON extraction from markdown code blocks
            json_match = re.search(r"```json\n(.*?)\n```", result, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                analysis = json.loads(json_str)
            elif "[SEARCH]" in result:
                search_query = result.split("[SEARCH]")[-1].strip()
                analysis = {"search": search_query}
            else:
                # Fallback for plain JSON object
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_str = result[json_start:json_end]
                    analysis = json.loads(json_str)
                else:
                    raise ValueError("No JSON object found in the output.")
        except (json.JSONDecodeError, IndexError, ValueError) as e:
            logger.error(f"Error parsing JSON output: {e}\nRaw model output:\n{result}")
            analysis = {"error": "Failed to parse JSON output from model."}
        return analysis
