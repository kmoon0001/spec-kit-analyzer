import logging
from typing import Dict, Any, Optional

from .document_processing_service import DocumentProcessingService
from .phi_scrubber import PhiScrubberService
from .compliance_analyzer import ComplianceAnalyzer
from .medicare_compliance_service import MedicareComplianceService
from .report_generator import ReportGenerator
from .clinical_entity_service import ClinicalEntityService
from .bias_detection_service import BiasDetectionService
from .quality_assurance_service import QualityAssuranceService
from .audit_trail_service import AuditTrailService

logger = logging.getLogger(__name__)


class ProcessingStep:
    def __init__(self, name: str, func, *args, **kwargs):
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def execute(self, context: Dict[str, Any]) -> Any:
        try:
            logger.info(f"Executing step: {self.name}")
            # Pass the whole context to the step function
            result = self.func(context, *self.args, **self.kwargs)
            # The step function should return the updated context
            return result
        except Exception as e:
            logger.error(f"Error in step '{self.name}': {e}", exc_info=True)
            raise


class DocumentProcessingPipeline:
    def __init__(
        self,
        document_processing_service: DocumentProcessingService,
        phi_scrubber_service: PhiScrubberService,
        clinical_entity_service: ClinicalEntityService,
        compliance_analyzer: ComplianceAnalyzer,
        medicare_compliance_service: MedicareComplianceService,
        bias_detection_service: BiasDetectionService,
        quality_assurance_service: QualityAssuranceService,
        audit_trail_service: AuditTrailService,
        report_generator: ReportGenerator,
    ):
        self.document_processing_service = document_processing_service
        self.phi_scrubber_service = phi_scrubber_service
        self.clinical_entity_service = clinical_entity_service
        self.compliance_analyzer = compliance_analyzer
        self.medicare_compliance_service = medicare_compliance_service
        self.bias_detection_service = bias_detection_service
        self.quality_assurance_service = quality_assurance_service
        self.audit_trail_service = audit_trail_service
        self.report_generator = report_generator
        self.steps = self._build_pipeline()

    def _build_pipeline(self) -> list[ProcessingStep]:
        return [
            ProcessingStep("load_text", self._load_text),
            ProcessingStep("redact_phi", self._redact_phi),
            ProcessingStep("extract_and_normalize_entities", self._extract_and_normalize_entities),
            ProcessingStep("analyze_compliance", self._analyze_compliance),
            ProcessingStep("calculate_medicare_score", self._calculate_medicare_score),
            ProcessingStep("detect_bias_in_recommendations", self._detect_bias_in_recommendations),
            ProcessingStep("perform_quality_assurance_checks", self._perform_quality_assurance_checks),
            ProcessingStep("generate_report", self._generate_report),
        ]

    def run(self, file_path: str, file_type: str) -> Optional[Dict[str, Any]]:
        self.audit_trail_service.log_pipeline_start(file_path, file_type)
        context = {"file_path": file_path, "file_type": file_type}
        try:
            for step in self.steps:
                try:
                    context = step.execute(context)
                    if context is None:
                        error_msg = f"Pipeline halted at step '{step.name}' because it returned None."
                        logger.warning(error_msg)
                        self.audit_trail_service.log_step(step.name, context, "failure", error=error_msg)
                        context = {"error": error_msg}
                        return context
                    self.audit_trail_service.log_step(step.name, context, "success")
                except Exception as e:
                    error_msg = f"Pipeline failed at step '{step.name}': {e}"
                    logger.error(error_msg)
                    self.audit_trail_service.log_step(step.name, context, "failure", error=str(e))
                    context["error"] = error_msg
                    return context
            return context
        finally:
            self.audit_trail_service.log_pipeline_end(context)

    def _load_text(self, context: Dict[str, Any]) -> Dict[str, Any]:
        file_path = context["file_path"]
        file_type = context["file_type"]
        text = self.document_processing_service.process_document(file_path, file_type)
        context["original_text"] = text
        return context

    def _redact_phi(self, context: Dict[str, Any]) -> Dict[str, Any]:
        text = context["original_text"]
        redacted_text = self.phi_scrubber_service.scrub_text(text)
        context["redacted_text"] = redacted_text
        return context

    def _extract_and_normalize_entities(self, context: Dict[str, Any]) -> Dict[str, Any]:
        text = context["redacted_text"]
        entities = self.clinical_entity_service.extract_and_normalize_entities(text)
        context["entities"] = entities
        return context

    def _analyze_compliance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        text = context["redacted_text"]
        entities = context.get("entities", [])

        # In a real scenario, more context would be passed
        # For now, we'll just pass the text and assume the analyzer can use it.
        # A more advanced implementation would pass the structured entities.
        analysis = self.compliance_analyzer.analyze_document(text, "OT", "Progress Note")
        analysis["extracted_entities"] = entities
        context["analysis"] = analysis
        return context

    def _calculate_medicare_score(self, context: Dict[str, Any]) -> Dict[str, Any]:
        analysis = context["analysis"]
        findings = analysis.get("findings", [])
        medicare_score_details = self.medicare_compliance_service.score_document(findings)
        context["medicare_score"] = medicare_score_details
        context["analysis"]["compliance_score"] = medicare_score_details["score"]
        return context

    def _detect_bias_in_recommendations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        analysis = context["analysis"]
        findings = analysis.get("findings", [])
        bias_results = self.bias_detection_service.detect_bias(findings)
        context["bias_analysis"] = bias_results
        return context

    def _perform_quality_assurance_checks(self, context: Dict[str, Any]) -> Dict[str, Any]:
        entities = context.get("entities", [])
        findings = context.get("analysis", {}).get("findings", [])
        qa_issues = self.quality_assurance_service.check_consistency(entities, findings)
        context["qa_issues"] = qa_issues
        return context

    def _generate_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        analysis_result = context["analysis"]
        analysis_result["bias_analysis"] = context.get("bias_analysis", [])
        analysis_result["qa_issues"] = context.get("qa_issues", [])
        report = self.report_generator.generate_report(analysis_result=analysis_result)
        context["report"] = report
        return context