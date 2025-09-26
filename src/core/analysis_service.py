import os
import yaml
import logging
import pickle
from src.parsing import parse_document_content

<<<<<<< HEAD
# Corrected imports to reflect refactoring
from .compliance_analyzer import ComplianceAnalyzer
from .hybrid_retriever import HybridRetriever
||||||| c46cdd8
# Corrected imports to reflect refactoring
from .llm_analyzer import LLMComplianceAnalyzer
from .hybrid_retriever import HybridRetriever
=======
# Import all the necessary services
from .compliance_analyzer import ComplianceAnalyzer
from .retriever import HybridRetriever
>>>>>>> origin/main
from .report_generator import ReportGenerator
from .document_classifier import DocumentClassifier
from .llm_service import LLMService
from .ner import NERPipeline
from .explanation import ExplanationEngine
from .prompt_manager import PromptManager
from .fact_checker_service import FactCheckerService # New Import

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class AnalysisService:
    """
    The central orchestrator for the entire analysis pipeline.
    Initializes and holds all AI-related services.
    """
    def __init__(self, retriever: HybridRetriever):
        logger.info("Initializing AnalysisService with injected retriever...")
        self.retriever = retriever
        try:
            config_path = os.path.join(ROOT_DIR, "config.yaml")
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # 1. Initialize the core AI models and services
            llm_service = LLMService(
                model_repo_id=config['models']['generator'],
                model_filename=config['models'].get('generator_filename'),
                llm_settings=config.get('llm_settings', {})
            )
<<<<<<< HEAD
            self.fact_checker_service = FactCheckerService(model_name=config['models']['fact_checker'])
            self.ner_pipeline = NERPipeline(model_names=config['models']['ner_ensemble'])
            self.retriever = HybridRetriever()
            self.preprocessing_service = PreprocessingService()
||||||| c46cdd8
            self.fact_checker_service = FactCheckerService(model_name=config['models']['fact_checker'])
            # Temporarily adjust constructor call to match placeholder
            self.ner_pipeline = NERPipeline(model_name="placeholder_for_ensemble")
            self.retriever = HybridRetriever()
            self.preprocessing_service = PreprocessingService()
=======
            fact_checker_service = FactCheckerService(model_name=config['models']['fact_checker'])
            ner_pipeline = NERPipeline(model_names=config['models']['ner_ensemble'])
>>>>>>> origin/main
            self.report_generator = ReportGenerator()
<<<<<<< HEAD
            self.explanation_engine = ExplanationEngine()
            self.nlg_service = NLGService()
||||||| c46cdd8
            self.explanation_engine = ExplanationEngine()
=======
            explanation_engine = ExplanationEngine()
>>>>>>> origin/main

            self.document_classifier = DocumentClassifier(
                llm_service=llm_service,
                prompt_template_path=os.path.join(ROOT_DIR, config['models']['doc_classifier_prompt'])
            )

            analysis_prompt_manager = PromptManager(
                template_path=os.path.join(ROOT_DIR, config['models']['analysis_prompt_template'])
            )

<<<<<<< HEAD
            # 2. Initialize the compliance analyzer with all its dependencies
            self.analyzer = ComplianceAnalyzer(
                retriever=self.retriever,
                ner_pipeline=self.ner_pipeline,
||||||| c46cdd8
            # 2. Initialize the new LLM analyzer instead of the old one
            self.llm_analyzer = LLMComplianceAnalyzer(
=======
            # 2. Initialize the main analyzer, passing it all the pre-loaded components
            self.analyzer = ComplianceAnalyzer(
                retriever=self.retriever,
                ner_pipeline=ner_pipeline,
>>>>>>> origin/main
                llm_service=llm_service,
<<<<<<< HEAD
                explanation_engine=self.explanation_engine,
||||||| c46cdd8
=======
                explanation_engine=explanation_engine,
>>>>>>> origin/main
                prompt_manager=analysis_prompt_manager,
<<<<<<< HEAD
                fact_checker_service=self.fact_checker_service
||||||| c46cdd8
=======
                fact_checker_service=fact_checker_service
>>>>>>> origin/main
            )
            logger.info("AnalysisService initialized successfully.")

        except Exception as e:
            logger.error(f"FATAL: Failed to initialize AnalysisService: {e}", exc_info=True)
            raise e

    def get_document_embedding(self, text: str) -> bytes:
        if not self.retriever or not self.retriever.dense_retriever:
            raise RuntimeError("Dense retriever is not initialized.")
        embedding = self.retriever.dense_retriever.encode(text)
        return pickle.dumps(embedding)

    def analyze_document(self, file_path: str, discipline: str) -> dict:
        """
        Performs a compliance analysis on a given document.
        This service acts as a high-level orchestrator, delegating tasks
        to specialized components.
        """
        doc_name = os.path.basename(file_path)
        logger.info(f"Starting analysis for document: {doc_name}")

        # 1. Parse and preprocess the document content
        document_text = " ".join([chunk['sentence'] for chunk in parse_document_content(file_path)])

        # Preprocessing step removed as the service is obsolete
        corrected_text = document_text

        # 2. Classify the document to understand its type (e.g., "Progress Note")
        doc_type = self.document_classifier.classify_document(corrected_text)
        logger.info(f"Document classified as: {doc_type}")

<<<<<<< HEAD
        # 3. Delegate the core analysis logic to the ComplianceAnalyzer
        # The analyzer handles NER, rule retrieval, LLM analysis, and fact-checking.
        analysis_result = self.analyzer.analyze_document(
            document_text=corrected_text,
            discipline=discipline,
            doc_type=doc_type
        )
||||||| c46cdd8
        entities = self.ner_pipeline.extract_entities(corrected_text)
        entity_list = ", ".join([f"{entity['entity_group']}: {entity['word']}" for entity in entities])
        search_query = f"{discipline} {doc_type} {entity_list}"
        retrieved_rules = self.retriever.retrieve(search_query)
=======
        analysis_result = self.analyzer.analyze_document(
            document_text=corrected_text,
            discipline=discipline,
            doc_type=doc_type
        )
>>>>>>> origin/main

<<<<<<< HEAD
        # 4. Generate a comprehensive report from the analysis findings
        final_report = self.report_generator.generate_report(
            original_text=document_text,
            analysis=analysis_result
        )

        return final_report
||||||| c46cdd8
        context = self._format_rules_for_prompt(retrieved_rules)

        analysis_result = self.llm_analyzer.analyze_document(document_text=corrected_text, context=context)

        explained_analysis = self.explanation_engine.add_explanations(analysis_result, corrected_text)

        if "findings" in explained_analysis:
            for finding in explained_analysis["findings"]:
                rule_id = finding.get("rule_id")
                associated_rule = next((r for r in retrieved_rules if r.get('id') == rule_id), None)

                if associated_rule:
                    if not self.fact_checker_service.is_finding_plausible(finding, associated_rule):
                        finding['is_disputed'] = True

                confidence = finding.get("confidence", 1.0)
                if isinstance(confidence, (int, float)) and confidence < CONFIDENCE_THRESHOLD:
                    finding['is_low_confidence'] = True

                tip = self.nlg_service.generate_personalized_tip(finding)
                finding['personalized_tip'] = tip

        return explained_analysis

    def _format_rules_for_prompt(self, rules: List[Dict[str, Any]]) -> str:
        if not rules:
            return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."
        return "\n".join([f"- Title: {r.get('name', '')}, Content: {r.g_et('content', '')}" for r in rules])
=======
        return analysis_result
>>>>>>> origin/main
