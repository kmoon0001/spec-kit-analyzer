"""AI Guardrails Service - Comprehensive Responsible AI Controls

This module implements comprehensive AI safety controls, bias mitigation,
transparency measures, and ethical guardrails for all AI-generated content
in the reporting system, ensuring safe, ethical, and trustworthy AI outputs.
"""

import hashlib
import logging
import re
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class GuardrailType(Enum):
    """Types of AI guardrails"""

    CONTENT_SAFETY = "content_safety"
    BIAS_DETECTION = "bias_detection"
    ACCURACY_VALIDATION = "accuracy_validation"
    ETHICAL_COMPLIANCE = "ethical_compliance"
    TRANSPARENCY_ENFORCEMENT = "transparency_enforcement"
    HALLUCINATION_DETECTION = "hallucination_detection"
    PROFESSIONAL_STANDARDS = "professional_standards"


class RiskLevel(Enum):
    """Risk levels for AI outputs"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(Enum):
    """Actions to take when guardrails are triggered"""

    ALLOW = "allow"
    MODIFY = "modify"
    FLAG = "flag"
    BLOCK = "block"
    ESCALATE = "escalate"


@dataclass
class GuardrailViolation:
    """Represents a guardrail violation"""

    guardrail_name: str
    violation_type: str
    severity: str
    message: str
    evidence: list[str]
    suggested_fix: str
    guardrail_type: GuardrailType = GuardrailType.CONTENT_SAFETY
    risk_level: RiskLevel = RiskLevel.MEDIUM
    confidence: float = 1.0
    suggested_action: ActionType = ActionType.FLAG

    def to_dict(self) -> dict[str, Any]:
        return {
            "guardrail_name": self.guardrail_name,
            "violation_type": self.violation_type,
            "severity": self.severity,
            "message": self.message,
            "evidence": self.evidence,
            "suggested_fix": self.suggested_fix,
            "guardrail_type": self.guardrail_type.value,
            "risk_level": self.risk_level.value,
            "confidence": self.confidence,
            "suggested_action": self.suggested_action.value,
        }


@dataclass
@dataclass
@dataclass
class GuardrailResult:
    """Result of guardrail evaluation"""

    content_id: str
    original_content: str
    modified_content: str | None
    violations: list[GuardrailViolation]
    overall_risk_level: RiskLevel
    action_taken: ActionType
    transparency_notes: list[str]
    confidence_adjustments: dict[str, float] = field(default_factory=dict)

    def is_safe(self) -> bool:
        """Check if content is safe for use"""
        return self.overall_risk_level in [
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
        ] and self.action_taken in [
            ActionType.ALLOW,
            ActionType.MODIFY,
            ActionType.FLAG,
        ]


class BaseGuardrail(ABC):
    """Abstract base class for all guardrails"""

    def __init__(self, name: str, description: str, enabled: bool = True):
        self.name = name
        self.description = description
        self.enabled = enabled
        self.violation_count = 0
        self.last_triggered: datetime | None = None

    @abstractmethod
    def evaluate(
        self, content: str, context: dict[str, Any]
    ) -> list[GuardrailViolation]:
        """Evaluate content against this guardrail"""

    def is_applicable(self, context: dict[str, Any]) -> bool:
        """Check if this guardrail applies to the given context"""
        return self.enabled


class ContentSafetyGuardrail(BaseGuardrail):
    """Guardrail for content safety and appropriateness"""

    def __init__(self):
        super().__init__(
            name="Content Safety",
            description="Ensures content is safe and appropriate for medical context",
        )

    def evaluate(
        self, content: str, context: dict[str, Any]
    ) -> list[GuardrailViolation]:
        """Evaluate content for safety violations"""
        violations = []

        # Check for harmful language
        harmful_language = self._get_harmful_language(content)
        if harmful_language:
            violations.append(
                GuardrailViolation(
                    guardrail_name=self.name,
                    violation_type="prohibited_content",
                    severity="high",
                    message="Content contains harmful or inappropriate language",
                    evidence=harmful_language,
                    suggested_fix="Remove or rephrase harmful language",
                    risk_level=RiskLevel.HIGH,
                    confidence=0.9,
                )
            )

        # Check for inappropriate medical claims
        inappropriate_claims = self._get_inappropriate_medical_claims(content)
        if inappropriate_claims:
            violations.append(
                GuardrailViolation(
                    guardrail_name=self.name,
                    violation_type="inappropriate_medical_claims",
                    severity="high",
                    message="Content contains inappropriate medical claims",
                    evidence=inappropriate_claims,
                    suggested_fix="Remove or qualify absolute medical claims",
                    confidence=0.8,
                )
            )

        return violations

    def _get_harmful_language(self, content: str) -> list[str]:
        """Check for harmful or inappropriate language."""
        harmful_patterns = [
            r"\b(?:kill|destroy|eliminate|annihilate).*?(?:pain|symptoms|condition)",
            r"\b(?:deadly|lethal|toxic|poisonous).*?(?:treatment|medication)",
            r"\b(?:dangerous|risky|harmful).*?(?:procedure|intervention)",
        ]

        evidence = []
        for pattern in harmful_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                evidence.append(match.group())
        return evidence

    def _get_inappropriate_medical_claims(self, content: str) -> list[str]:
        """Check for inappropriate medical claims and return evidence."""
        claim_patterns = [
            r"\b(?:will|shall|guaranteed to).*?(?:cure|heal|fix|resolve)",
            r"\b(?:always|never|100%|completely).*?(?:effective|successful)",
            r"\b(?:best|only|perfect).*?(?:treatment|solution|approach)",
        ]

        evidence = []
        for pattern in claim_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                evidence.append(match.group())
        return evidence


class BiasDetectionGuardrail(BaseGuardrail):
    """Guardrail for detecting and mitigating bias in AI outputs"""

    def __init__(self):
        super().__init__(
            name="Bias Detection",
            description="Detects and mitigates bias in AI-generated content",
        )

    def evaluate(
        self, content: str, context: dict[str, Any]
    ) -> list[GuardrailViolation]:
        """Evaluate content for bias violations"""
        violations = []

        # Check for demographic bias
        demographic_bias = self._get_demographic_bias(content)
        if demographic_bias:
            violations.append(
                GuardrailViolation(
                    guardrail_name=self.name,
                    violation_type="demographic_bias",
                    severity="high",
                    message="Content contains demographic bias or stereotyping",
                    evidence=demographic_bias,
                    suggested_fix="Remove generalizations about demographic groups",
                    guardrail_type=GuardrailType.BIAS_DETECTION,
                    risk_level=RiskLevel.HIGH,
                    confidence=0.8,
                )
            )

        # Check for socioeconomic bias
        socioeconomic_bias = self._get_socioeconomic_bias(content)
        if socioeconomic_bias:
            violations.append(
                GuardrailViolation(
                    guardrail_name=self.name,
                    violation_type="socioeconomic_bias",
                    severity="high",
                    message="Content contains socioeconomic bias or stereotyping",
                    evidence=socioeconomic_bias,
                    suggested_fix="Avoid generalizations about socioeconomic groups",
                    guardrail_type=GuardrailType.BIAS_DETECTION,
                    risk_level=RiskLevel.HIGH,
                    confidence=0.8,
                )
            )

        # Check for geographic bias
        geographic_bias = self._get_geographic_bias(content)
        if geographic_bias:
            violations.append(
                GuardrailViolation(
                    guardrail_name=self.name,
                    violation_type="geographic_bias",
                    severity="high",
                    message="Content contains geographic bias or stereotyping",
                    evidence=geographic_bias,
                    suggested_fix="Avoid generalizations about geographic regions",
                    guardrail_type=GuardrailType.BIAS_DETECTION,
                    risk_level=RiskLevel.HIGH,
                    confidence=0.8,
                )
            )

        # Check for overconfident statements
        overconfident_statements = self._get_overconfident_statements(content)
        if overconfident_statements:
            violations.append(
                GuardrailViolation(
                    guardrail_name=self.name,
                    violation_type="overconfident_statements",
                    severity="medium",
                    message="Content contains overconfident statements",
                    evidence=overconfident_statements,
                    suggested_fix="Add qualifiers and uncertainty indicators",
                    risk_level=RiskLevel.MEDIUM,
                    confidence=0.7,
                )
            )

        return violations

    def _get_demographic_bias(self, content: str) -> list[str]:
        """Check for demographic bias and stereotyping."""
        bias_patterns = [
            r"\b(?:all|most|many|typical|usually).*?(?:elderly|old|senior).*?(?:patients|people).*?(?:have|are|do)",
            r"\b(?:all|most|many|typical|usually).*?(?:young|teenage|adolescent).*?(?:patients|people).*?(?:have|are|do)",
            r"\b(?:all|most|many|typical|usually).*?(?:male|female|men|women).*?(?:patients|people).*?(?:have|are|do)",
        ]

        evidence = []
        for pattern in bias_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                evidence.append(match.group())
        return evidence

    def _get_socioeconomic_bias(self, content: str) -> list[str]:
        """Check for socioeconomic bias and stereotyping."""
        bias_patterns = [
            r"\b(?:all|most|many|typical|usually).*?(?:low-income|poor|wealthy|rich).*?(?:patients|people).*?(?:have|are|do)",
            r"\b(?:low-income|poor).*?(?:patients|people).*?(?:usually|typically|always|never).*?(?:have|are|do)",
            r"\b(?:wealthy|rich).*?(?:patients|people).*?(?:usually|typically|always|never).*?(?:have|are|do)",
        ]

        evidence = []
        for pattern in bias_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                evidence.append(match.group())
        return evidence

    def _get_geographic_bias(self, content: str) -> list[str]:
        """Check for geographic bias and stereotyping."""
        bias_patterns = [
            r"\b(?:rural|urban|city|country).*?(?:patients|people).*?(?:typically|usually|always|never).*?(?:have|are|do|lack)",
            r"\b(?:all|most|many|typical|usually).*?(?:rural|urban|city|country).*?(?:patients|people).*?(?:have|are|do)",
        ]

        evidence = []
        for pattern in bias_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                evidence.append(match.group())
        return evidence

    def _get_overconfident_statements(self, content: str) -> list[str]:
        """Check for overconfident statements and return evidence."""
        overconfident_patterns = [
            r"\b(?:definitely|certainly|absolutely|undoubtedly).*?(?:will|should|must)",
            r"\b(?:always|never|all|none|every).*?(?:patients|clients|cases)",
            r"\b(?:proven|established|confirmed).*?(?:fact|truth|reality)",
        ]

        evidence = []
        for pattern in overconfident_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                evidence.append(match.group())
        return evidence


class EthicalComplianceGuardrail(BaseGuardrail):
    """Guardrail for ensuring ethical compliance in healthcare AI"""

    def __init__(self):
        super().__init__(
            name="Ethical Compliance",
            description="Ensures content meets ethical standards for healthcare AI",
        )

    def evaluate(
        self, content: str, context: dict[str, Any]
    ) -> list[GuardrailViolation]:
        """Evaluate content for ethical compliance violations"""
        violations = []

        # Check for explicit ethical violations
        ethical_violations = self._detect_ethical_violations(content)
        if ethical_violations:
            violations.append(
                GuardrailViolation(
                    guardrail_name=self.name,
                    violation_type="ethical_violation",
                    severity="critical",
                    message="Content contains unethical recommendations or practices",
                    evidence=ethical_violations,
                    suggested_fix="Remove unethical content and ensure respect for patient autonomy and rights",
                    guardrail_type=GuardrailType.ETHICAL_COMPLIANCE,
                    risk_level=RiskLevel.CRITICAL,
                    confidence=0.9,
                    suggested_action=ActionType.BLOCK,
                )
            )

        # Check for missing ethical considerations
        if self._missing_ethical_considerations(content, context):
            violations.append(
                GuardrailViolation(
                    guardrail_name=self.name,
                    violation_type="missing_ethical_considerations",
                    severity="high",
                    message="Content lacks necessary ethical considerations",
                    evidence=["Missing ethical considerations for healthcare context"],
                    suggested_fix="Include references to patient autonomy, informed consent, or professional judgment",
                    guardrail_type=GuardrailType.ETHICAL_COMPLIANCE,
                    risk_level=RiskLevel.HIGH,
                    confidence=0.8,
                )
            )

        return violations

    def _missing_ethical_considerations(
        self, content: str, context: dict[str, Any]
    ) -> bool:
        """Check if content is missing ethical considerations"""
        # For high-stakes content, ensure ethical considerations are present
        if context.get("content_type") in [
            "recommendation",
            "treatment_plan",
            "diagnosis",
        ]:
            ethical_indicators = [
                "patient autonomy",
                "informed consent",
                "professional judgment",
                "individual circumstances",
                "clinical expertise",
            ]

            content_lower = content.lower()
            for indicator in ethical_indicators:
                if indicator in content_lower:
                    return False
            return True

        return False

    def _detect_ethical_violations(self, content: str) -> list[str]:
        """Detect explicit ethical violations in content"""
        violation_patterns = [
            r"\b(?:force|coerce|compel).*?(?:patient|client).*?(?:comply|accept|agree)",
            r"\b(?:regardless of|ignore|dismiss).*?(?:patient|their).*?(?:wishes|preferences|consent)",
            r"\b(?:withhold|hide|conceal).*?(?:information|diagnosis|prognosis).*?(?:from|patient)",
            r"\b(?:discriminate|bias|prejudice).*?(?:against|based on).*?(?:race|gender|age|religion)",
            r"\b(?:experimental|untested).*?(?:treatment|procedure).*?(?:without|no).*?(?:consent|approval)",
        ]

        violations = []
        for pattern in violation_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                violations.append(match.group())

        return violations


class TransparencyEnforcementGuardrail(BaseGuardrail):
    """Guardrail for enforcing AI transparency and explainability"""

    def __init__(self):
        super().__init__(
            name="Transparency Enforcement",
            description="Ensures AI-generated content includes proper transparency indicators",
        )
        self.transparency_requirements = {
            "ai_disclosure": [
                "ai-generated",
                "artificial intelligence",
                "automated analysis",
            ],
            "confidence_indicators": [
                "confidence",
                "uncertainty",
                "may",
                "might",
                "possibly",
            ],
            "human_oversight": [
                "professional judgment",
                "clinical expertise",
                "human review",
            ],
        }

    def evaluate(
        self, content: str, context: dict[str, Any]
    ) -> list[GuardrailViolation]:
        """Evaluate content for transparency violations"""
        if not content or content.isspace():
            return []
        violations = []

        # Check for missing transparency elements
        missing_elements = self._check_transparency_elements(content, context)

        # Create specific violations for each missing element
        if "ai_disclosure" in missing_elements:
            violations.append(
                GuardrailViolation(
                    guardrail_name=self.name,
                    violation_type="missing_ai_disclosure",
                    severity="high",
                    message="Content lacks AI disclosure statement",
                    evidence=["Missing AI-generated content disclosure"],
                    suggested_fix="Add clear indication that content is AI-generated",
                    guardrail_type=GuardrailType.TRANSPARENCY_ENFORCEMENT,
                    risk_level=RiskLevel.HIGH,
                    confidence=0.9,
                )
            )

        if "confidence_indicators" in missing_elements:
            violations.append(
                GuardrailViolation(
                    guardrail_name=self.name,
                    violation_type="missing_confidence_indicators",
                    severity="medium",
                    message="Content lacks confidence or uncertainty indicators",
                    evidence=["Missing confidence/uncertainty indicators"],
                    suggested_fix="Add confidence levels or uncertainty qualifiers",
                    guardrail_type=GuardrailType.TRANSPARENCY_ENFORCEMENT,
                    risk_level=RiskLevel.MEDIUM,
                    confidence=0.8,
                )
            )

        if "human_oversight" in missing_elements:
            violations.append(
                GuardrailViolation(
                    guardrail_name=self.name,
                    violation_type="missing_human_oversight",
                    severity="medium",
                    message="Content lacks human oversight references",
                    evidence=[
                        "Missing human oversight or professional judgment references"
                    ],
                    suggested_fix="Add references to professional judgment or human review",
                    guardrail_type=GuardrailType.TRANSPARENCY_ENFORCEMENT,
                    risk_level=RiskLevel.MEDIUM,
                    confidence=0.7,
                )
            )

        return violations

    def _check_transparency_elements(
        self, content: str, context: dict[str, Any]
    ) -> list[str]:
        """Check which transparency elements are missing"""
        missing = []
        content_lower = content.lower()

        # Check if this is AI-generated content that needs transparency
        if context.get("ai_generated", True):
            for element, indicators in self.transparency_requirements.items():
                if not any(indicator in content_lower for indicator in indicators):
                    missing.append(element)

        return missing


class AIGuardrailsService:
    """Main service for AI guardrails and responsible AI controls"""

    def __init__(self):
        self.guardrails = []
        self.violation_history = []
        self.transparency_templates = self._load_transparency_templates()
        self._initialize_default_guardrails()

    def _initialize_default_guardrails(self) -> None:
        """Initialize default set of guardrails"""
        self.guardrails = [
            ContentSafetyGuardrail(),
            BiasDetectionGuardrail(),
            AccuracyValidationGuardrail(),
            EthicalComplianceGuardrail(),
            TransparencyEnforcementGuardrail(),
        ]

        logger.info("Initialized %s AI guardrails", len(self.guardrails))

    def _load_transparency_templates(self) -> dict[str, str]:
        """Load transparency statement templates"""
        return {
            "ai_disclosure": "This content was generated using artificial intelligence and should be reviewed by qualified professionals.",
            "confidence_low": "This analysis has low confidence and requires additional verification.",
            "confidence_medium": "This analysis has moderate confidence and should be validated by clinical expertise.",
            "confidence_high": "This analysis has high confidence but still requires professional judgment.",
            "limitations": "AI analysis has limitations and may not capture all relevant clinical factors.",
            "human_oversight": "Professional clinical judgment is required to validate and act upon these findings.",
        }

    def evaluate_content(
        self, content: str, context: dict[str, Any]
    ) -> GuardrailResult:
        """Evaluate content against all applicable guardrails"""
        content_id = self._generate_content_id(content)
        all_violations: list[GuardrailViolation] = []

        # Run all applicable guardrails
        for guardrail in self.guardrails:
            if guardrail.is_applicable(context):
                try:
                    violations = guardrail.evaluate(content, context)
                    all_violations.extend(violations)

                    if violations:
                        guardrail.violation_count += len(violations)
                        guardrail.last_triggered = datetime.now()

                except Exception:
                    logger.exception("Error in guardrail %s: {e}", guardrail.name)

        # Determine overall risk level and action
        overall_risk = self._calculate_overall_risk(all_violations)
        action_taken = self._determine_action(all_violations, overall_risk)

        # Apply modifications if needed
        modified_content = self._apply_modifications(content, all_violations, context)

        # Generate transparency notes
        transparency_notes = self._generate_transparency_notes(all_violations, context)

        # Calculate confidence adjustments
        confidence_adjustments = self._calculate_confidence_adjustments(all_violations)

        result = GuardrailResult(
            content_id=content_id,
            original_content=content,
            modified_content=modified_content,
            violations=all_violations,
            overall_risk_level=overall_risk,
            action_taken=action_taken,
            transparency_notes=transparency_notes,
            confidence_adjustments=confidence_adjustments,
        )

        # Store result for audit trail
        self.violation_history.append(result)

        logger.info(
            "Guardrail evaluation complete: %s violations, ",
            len(all_violations),
            f"risk level: {overall_risk.value}, action: {action_taken.value}",
        )

        return result

    def _generate_content_id(self, content: str) -> str:
        """Generate unique ID for content"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _calculate_overall_risk(
        self, violations: list[GuardrailViolation]
    ) -> RiskLevel:
        """Calculate overall risk level from violations"""
        if not violations:
            return RiskLevel.LOW

        # Count violations by risk level
        risk_counts = Counter(v.risk_level for v in violations)

        if risk_counts[RiskLevel.CRITICAL] > 0:
            return RiskLevel.CRITICAL
        if risk_counts[RiskLevel.HIGH] > 0:
            return RiskLevel.HIGH
        if (
            risk_counts[RiskLevel.MEDIUM] > 2
        ):  # Multiple medium risks = high overall risk
            return RiskLevel.HIGH
        if risk_counts[RiskLevel.MEDIUM] > 0:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _determine_action(
        self, violations: list[GuardrailViolation], overall_risk: RiskLevel
    ) -> ActionType:
        """Determine action to take based on violations and risk level"""
        if overall_risk == RiskLevel.CRITICAL:
            return ActionType.BLOCK
        if overall_risk == RiskLevel.HIGH:
            # Check if any violations require blocking
            if any(v.suggested_action == ActionType.BLOCK for v in violations):
                return ActionType.BLOCK
            return ActionType.MODIFY
        if overall_risk == RiskLevel.MEDIUM:
            return ActionType.MODIFY
        return ActionType.ALLOW

    def _apply_modifications(
        self,
        content: str,
        violations: list[GuardrailViolation],
        context: dict[str, Any],
    ) -> str | None:
        """Apply modifications to content based on violations"""
        if not violations:
            return None

        modified_content = content

        # Apply specific modifications based on violation types
        for violation in violations:
            if violation.suggested_action in [ActionType.MODIFY, ActionType.FLAG]:
                modified_content = self._apply_specific_modification(
                    modified_content, violation, context
                )

        # Add transparency statements
        modified_content = self._add_transparency_statements(
            modified_content, violations, context
        )

        return modified_content if modified_content != content else None

    def _apply_specific_modification(
        self, content: str, violation: GuardrailViolation, context: dict[str, Any]
    ) -> str:
        """Apply specific modification for a violation"""
        if violation.guardrail_type == GuardrailType.BIAS_DETECTION:
            # Apply inclusive language modifications
            for evidence in violation.evidence:
                if "typical patient" in evidence.lower():
                    content = content.replace(evidence, "patients")
                elif "all women" in evidence.lower():
                    content = content.replace(evidence, "some women")
                # Add more specific replacements as needed

        elif violation.guardrail_type == GuardrailType.ACCURACY_VALIDATION:
            # Add uncertainty qualifiers
            if "definitely" in content.lower():
                content = re.sub(
                    r"\bdefinitely\b", "likely", content, flags=re.IGNORECASE
                )
            if "always" in content.lower():
                content = re.sub(
                    r"\balways\b", "typically", content, flags=re.IGNORECASE
                )

        elif violation.guardrail_type == GuardrailType.CONTENT_SAFETY:
            # Apply safety modifications
            for evidence in violation.evidence:
                # Replace with safer alternatives
                content = content.replace(evidence, "[CONTENT MODIFIED FOR SAFETY]")

        return content

    def _add_transparency_statements(
        self,
        content: str,
        violations: list[GuardrailViolation],
        context: dict[str, Any],
    ) -> str:
        """Add transparency statements to content"""
        transparency_additions = []

        # Add AI disclosure if missing
        if any(v.violation_type == "missing_ai_disclosure" for v in violations):
            transparency_additions.append(self.transparency_templates["ai_disclosure"])

        # Add confidence indicators
        confidence_level = context.get("confidence_level", "medium")
        if confidence_level in self.transparency_templates:
            transparency_additions.append(self.transparency_templates[confidence_level])

        # Add limitations disclosure
        if any(v.violation_type == "missing_limitations" for v in violations):
            transparency_additions.append(self.transparency_templates["limitations"])

        # Add human oversight requirement
        if any(v.violation_type == "missing_human_oversight" for v in violations):
            transparency_additions.append(
                self.transparency_templates["human_oversight"]
            )

        # Append transparency statements
        if transparency_additions:
            transparency_section = "\n\n**AI Transparency Notice:**\n" + "\n".join(
                f"• {statement}" for statement in transparency_additions
            )
            content += transparency_section

        return content

    def _generate_transparency_notes(
        self, violations: list[GuardrailViolation], context: dict[str, Any]
    ) -> list[str]:
        """Generate transparency notes for the evaluation"""
        notes = []

        if violations:
            notes.append(f"AI guardrails detected {len(violations)} potential issues")

            # Group violations by type
            violation_types: Counter[GuardrailType] = Counter(
                v.guardrail_type for v in violations
            )
            for guardrail_type, count in violation_types.items():
                notes.append(f"{guardrail_type.value}: {count} issues detected")

        # Add confidence information
        if "confidence_level" in context:
            notes.append(f"AI confidence level: {context['confidence_level']}")

        # Add model information
        if "model_name" in context:
            notes.append(f"Generated by: {context['model_name']}")

        return notes

    def _calculate_confidence_adjustments(
        self, violations: list[GuardrailViolation]
    ) -> dict[str, float]:
        """Calculate confidence adjustments based on violations"""
        adjustments = {}

        # Reduce confidence based on violation types
        for violation in violations:
            if violation.guardrail_type == GuardrailType.HALLUCINATION_DETECTION:
                adjustments["hallucination_penalty"] = -0.3
            elif violation.guardrail_type == GuardrailType.ACCURACY_VALIDATION:
                adjustments["accuracy_penalty"] = -0.2
            elif violation.guardrail_type == GuardrailType.BIAS_DETECTION:
                adjustments["bias_penalty"] = -0.1

        return adjustments

    def get_guardrail_statistics(self) -> dict[str, Any]:
        """Get statistics about guardrail performance"""
        total_evaluations = len(self.violation_history)
        total_violations = sum(
            len(result.violations) for result in self.violation_history
        )

        # Calculate violation rates by type
        violation_types: dict[str, int] = defaultdict(int)
        for result in self.violation_history:
            for violation in result.violations:
                violation_types[violation.guardrail_type.value] += 1

        # Calculate risk level distribution
        risk_levels = Counter(
            result.overall_risk_level for result in self.violation_history
        )

        # Calculate action distribution
        actions = Counter(result.action_taken for result in self.violation_history)

        return {
            "total_evaluations": total_evaluations,
            "total_violations": total_violations,
            "violation_rate": total_violations / max(total_evaluations, 1),
            "violation_types": dict(violation_types),
            "risk_level_distribution": {
                level.value: count for level, count in risk_levels.items()
            },
            "action_distribution": {
                action.value: count for action, count in actions.items()
            },
            "guardrail_status": [
                {
                    "name": g.name,
                    "enabled": g.enabled,
                    "violation_count": g.violation_count,
                    "last_triggered": (
                        g.last_triggered.isoformat() if g.last_triggered else None
                    ),
                }
                for g in self.guardrails
            ],
        }

    def enable_guardrail(self, guardrail_name: str) -> bool:
        """Enable a specific guardrail"""
        for guardrail in self.guardrails:
            if guardrail.name == guardrail_name:
                guardrail.enabled = True
                logger.info("Enabled guardrail: %s", guardrail_name)
                return True
        return False

    def disable_guardrail(self, guardrail_name: str) -> bool:
        """Disable a specific guardrail"""
        for guardrail in self.guardrails:
            if guardrail.name == guardrail_name:
                guardrail.enabled = False
                logger.info("Disabled guardrail: %s", guardrail_name)
                return True
        return False

    def add_custom_guardrail(self, guardrail: BaseGuardrail) -> None:
        """Add a custom guardrail"""
        self.guardrails.append(guardrail)
        logger.info("Added custom guardrail: %s", guardrail.name)

    def clear_violation_history(self) -> None:
        """Clear violation history (for privacy/storage management)"""
        self.violation_history.clear()
        logger.info("Cleared guardrail violation history")


class AccuracyValidationGuardrail(BaseGuardrail):
    """Accuracy validation guardrail."""

    def __init__(self):
        super().__init__(
            name="Accuracy Validation",
            description="Validates content accuracy and identifies potential hallucinations",
        )

    def evaluate(
        self, content: str, context: dict[str, Any]
    ) -> list[GuardrailViolation]:
        """Evaluate content for accuracy issues"""
        violations = []

        # Check for potential hallucinations
        hallucinations = self._get_potential_hallucinations(content)
        if hallucinations:
            violations.append(
                GuardrailViolation(
                    guardrail_name=self.name,
                    violation_type="potential_hallucination",
                    severity="high",
                    message="Content may contain hallucinated or unverifiable claims",
                    evidence=hallucinations,
                    suggested_fix="Verify claims with reliable sources",
                    guardrail_type=GuardrailType.ACCURACY_VALIDATION,
                    risk_level=RiskLevel.HIGH,
                    confidence=0.7,
                )
            )

        # Check for overconfident statements
        overconfident = self._get_overconfident_medical_statements(content)
        if overconfident:
            violations.append(
                GuardrailViolation(
                    guardrail_name=self.name,
                    violation_type="overconfident_statement",
                    severity="medium",
                    message="Content contains overconfident medical statements",
                    evidence=overconfident,
                    suggested_fix="Add qualifiers and uncertainty indicators",
                    guardrail_type=GuardrailType.ACCURACY_VALIDATION,
                    risk_level=RiskLevel.MEDIUM,
                    confidence=0.8,
                )
            )

        return violations

    def _get_potential_hallucinations(self, content: str) -> list[str]:
        """Check for potential hallucinations or unverifiable claims."""
        hallucination_patterns = [
            r"\b(?:studies show|research proves|scientists discovered).*?(?:without|no evidence|unproven)",
            r"\b(?:new breakthrough|revolutionary|miracle).*?(?:treatment|cure|therapy)",
            r"\b(?:100%|completely|totally).*?(?:safe|effective|guaranteed)",
            r"\b(?:recent|new|latest).*?(?:FDA|research|study).*?(?:published|shows|proves).*?(?:last week|yesterday|today)",  # Recent unverifiable claims
            r"\b(?:95\.\d+%|9[0-9]\.\d+%).*?(?:effectiveness|success|cure)",  # Suspiciously precise statistics
            r"\b(?:according to|based on).*?(?:recent|new|unpublished).*?(?:research|study|findings)",  # Vague source references
        ]

        evidence = []
        for pattern in hallucination_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                evidence.append(match.group())
        return evidence

    def _get_overconfident_medical_statements(self, content: str) -> list[str]:
        """Check for overconfident medical statements."""
        overconfident_patterns = [
            r"\b(?:definitely|certainly|absolutely).*?(?:will|must|should).*?(?:improve|heal|cure|work)",
            r"\b(?:always|never|all patients|every case).*?(?:respond|react|improve)",
            r"\b(?:proven|established|confirmed).*?(?:to work|effective|successful)",
            r"\b(?:shows|demonstrates).*?(?:9[0-9]\.\d+%|95\.\d+%).*?(?:effectiveness|success)",  # Suspiciously precise claims
            r"\b(?:this|the).*?(?:treatment|therapy).*?(?:shows|demonstrates|proves).*?(?:high|significant).*?(?:effectiveness|success)",  # Overconfident treatment claims
            r"\b(?:will|must).*?(?:definitely|certainly).*?(?:work|succeed|cure).*?(?:all|every).*?(?:patients|cases)",  # Definitive claims about all patients
            r"\b(?:all patients|every patient).*?(?:without exception|guaranteed|always)",  # Universal patient claims
        ]

        evidence = []
        for pattern in overconfident_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                evidence.append(match.group())
        return evidence
