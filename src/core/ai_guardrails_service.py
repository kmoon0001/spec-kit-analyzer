"""
AI Guardrails Service - Comprehensive Responsible AI Controls

This module implements comprehensive AI safety controls, bias mitigation,
transparency measures, and ethical guardrails for all AI-generated content
in the reporting system, ensuring safe, ethical, and trustworthy AI outputs.
"""

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
from collections import defaultdict, Counter

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
    guardrail_type: GuardrailType
    violation_type: str
    description: str
    risk_level: RiskLevel
    confidence: float
    evidence: List[str]
    suggested_action: ActionType
    mitigation_strategy: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "guardrail_type": self.guardrail_type.value,
            "violation_type": self.violation_type,
            "description": self.description,
            "risk_level": self.risk_level.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "suggested_action": self.suggested_action.value,
            "mitigation_strategy": self.mitigation_strategy
        }


@dataclass
class GuardrailResult:
    """Result of guardrail evaluation"""
    content_id: str
    original_content: str
    modified_content: Optional[str]
    violations: List[GuardrailViolation]
    overall_risk_level: RiskLevel
    action_taken: ActionType
    transparency_notes: List[str]
    confidence_adjustments: Dict[str, float] = field(default_factory=dict)
    
    def is_safe(self) -> bool:
        """Check if content is safe for use"""
        return self.overall_risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM] and \
               self.action_taken in [ActionType.ALLOW, ActionType.MODIFY, ActionType.FLAG]


class BaseGuardrail(ABC):
    """Abstract base class for all guardrails"""
    
    def __init__(self, name: str, description: str, enabled: bool = True):
        self.name = name
        self.description = description
        self.enabled = enabled
        self.violation_count = 0
        self.last_triggered: Optional[datetime] = None
    
    @abstractmethod
    def evaluate(self, content: str, context: Dict[str, Any]) -> List[GuardrailViolation]:
        """Evaluate content against this guardrail"""
        pass
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if this guardrail applies to the given context"""
        return self.enabled


class ContentSafetyGuardrail(BaseGuardrail):
    """Guardrail for content safety and appropriateness"""
    
    def __init__(self):
        super().__init__(
            "Content Safety",
            "Ensures AI-generated content is safe and appropriate for healthcare settings"
        )
        
        # Define prohibited content patterns
        self.prohibited_patterns = [
            r'\b(?:kill|die|death|suicide|harm)\b.*(?:patient|client|individual)',
            r'\b(?:illegal|unlawful|criminal)\b.*(?:activity|action|behavior)',
            r'\b(?:discriminat|racist|sexist|homophobic)\b',
            r'\b(?:personal|private|confidential)\s+(?:information|data)\b',
            r'\b(?:guarantee|promise|ensure)\s+(?:cure|recovery|outcome)',
        ]
        
        # Define sensitive medical terms requiring careful handling
        self.sensitive_terms = [
            'diagnosis', 'prognosis', 'treatment plan', 'medication',
            'surgery', 'procedure', 'condition', 'disorder'
        ]
    
    def evaluate(self, content: str, context: Dict[str, Any]) -> List[GuardrailViolation]:
        violations = []
        
        # Check for prohibited patterns
        for pattern in self.prohibited_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                violations.append(GuardrailViolation(
                    guardrail_type=GuardrailType.CONTENT_SAFETY,
                    violation_type="prohibited_content",
                    description=f"Content contains potentially harmful language: '{match.group()}'",
                    risk_level=RiskLevel.HIGH,
                    confidence=0.9,
                    evidence=[match.group()],
                    suggested_action=ActionType.MODIFY,
                    mitigation_strategy="Replace with professional, neutral language"
                ))
        
        # Check for inappropriate medical claims
        if self._contains_inappropriate_medical_claims(content):
            violations.append(GuardrailViolation(
                guardrail_type=GuardrailType.CONTENT_SAFETY,
                violation_type="inappropriate_medical_claims",
                description="Content contains inappropriate medical claims or guarantees",
                risk_level=RiskLevel.MEDIUM,
                confidence=0.8,
                evidence=["Medical claims detected"],
                suggested_action=ActionType.MODIFY,
                mitigation_strategy="Add appropriate disclaimers and qualify statements"
            ))
        
        return violations
    
    def _contains_inappropriate_medical_claims(self, content: str) -> bool:
        """Check for inappropriate medical claims"""
        claim_patterns = [
            r'\b(?:will|shall|guaranteed to)\s+(?:\w+\s+){0,3}?(?:cure|heal|fix|resolve)',
            r'\b(?:always|never|100%|completely)\s+(?:effective|successful)',
            r'\b(?:best|only|perfect)\s+(?:treatment|solution|approach)'
        ]
        
        for pattern in claim_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False


class BiasDetectionGuardrail(BaseGuardrail):
    """Guardrail for detecting and mitigating bias in AI outputs"""
    
    def __init__(self):
        super().__init__(
            "Bias Detection",
            "Detects and mitigates potential bias in AI-generated content"
        )
        
        # Define bias indicators
        self.bias_indicators = {
            'demographic': [
                r'\b(?:typical|normal|standard)\s+(?:patient|client|individual)',
                r'\b(?:all|most|many)\s+(?:women|men|elderly|young)\s+(?:are|have|do|typically)',
                r'\b(?:cultural|ethnic|racial)\s+(?:factors|issues|problems)',
                r'\ball\s+elderly\s+patients\s+typically'
            ],
            'socioeconomic': [
                r'\b(?:low-income|poor|wealthy|rich)\s+(?:patients|clients)',
                r'\b(?:education level|social status)\s+(?:affects|determines|causes)',
                r'\b(?:compliance|adherence)\s+(?:issues|problems)\s+(?:in|among)\s+(?:certain|specific)\s+(?:groups|populations)'
            ],
            'geographic': [
                r'\b(?:urban|rural|suburban)\s+(?:patients|populations)\s+(?:typically|usually|often)',
                r'\b(?:regional|local|area)\s+(?:differences|variations)\s+(?:in|of)\s+(?:care|treatment)'
            ]
        }
        
        # Define inclusive language alternatives
        self.inclusive_alternatives = {
            'typical patient': 'patients',
            'normal individual': 'individuals',
            'standard client': 'clients',
            'all women': 'some women',
            'most men': 'many men',
            'elderly patients': 'older adult patients'
        }
    
    def evaluate(self, content: str, context: Dict[str, Any]) -> List[GuardrailViolation]:
        violations = []
        
        for bias_type, patterns in self.bias_indicators.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    violations.append(GuardrailViolation(
                        guardrail_type=GuardrailType.BIAS_DETECTION,
                        violation_type=f"{bias_type}_bias",
                        description=f"Potential {bias_type} bias detected: '{match.group()}'",
                        risk_level=RiskLevel.MEDIUM,
                        confidence=0.7,
                        evidence=[match.group()],
                        suggested_action=ActionType.MODIFY,
                        mitigation_strategy=f"Use more inclusive language that doesn't generalize about {bias_type} groups"
                    ))
        
        return violations


class AccuracyValidationGuardrail(BaseGuardrail):
    """Guardrail for validating accuracy and preventing hallucinations"""
    
    def __init__(self):
        super().__init__(
            "Accuracy Validation",
            "Validates accuracy of AI-generated content and detects potential hallucinations"
        )
        
        # Define patterns that indicate potential hallucinations
        self.hallucination_indicators = [
            r'\b(?:according to|based on|research shows|studies indicate)\s+(?:recent|new|latest)\s+(?:\w+\s+){0,3}?(?:research|study|findings)',
            r'\b(?:FDA|CMS|Medicare)\s+(?:recently|just|newly)\s+(?:approved|released|published)',
            r'\b(?:specific|exact|precise)\s+(?:percentage|number|statistic)\s+(?:of|for|in)',
            r'\b(?:Dr\.|Professor|Expert)\s+[A-Z][a-z]+\s+(?:states|says|recommends|suggests)',
            r'\b(?:version|update|revision)\s+\d+\.\d+\s+(?:of|for)',
        ]
        
        # Define confidence-reducing patterns
        self.uncertainty_patterns = [
            r'\b(?:might|may|could|possibly|potentially|likely)\b',
            r'\b(?:appears|seems|suggests|indicates)\b',
            r'\b(?:in some cases|sometimes|occasionally)\b'
        ]
    
    def evaluate(self, content: str, context: Dict[str, Any]) -> List[GuardrailViolation]:
        violations = []
        
        # Check for potential hallucinations
        for pattern in self.hallucination_indicators:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                violations.append(GuardrailViolation(
                    guardrail_type=GuardrailType.HALLUCINATION_DETECTION,
                    violation_type="potential_hallucination",
                    description=f"Potential hallucination detected: '{match.group()}'",
                    risk_level=RiskLevel.HIGH,
                    confidence=0.8,
                    evidence=[match.group()],
                    suggested_action=ActionType.FLAG,
                    mitigation_strategy="Verify factual claims against trusted sources and add appropriate disclaimers"
                ))
        
        # Check for overconfident statements
        if self._contains_overconfident_statements(content):
            violations.append(GuardrailViolation(
                guardrail_type=GuardrailType.ACCURACY_VALIDATION,
                violation_type="overconfident_statements",
                description="Content contains overconfident statements without appropriate qualifiers",
                risk_level=RiskLevel.MEDIUM,
                confidence=0.7,
                evidence=["Overconfident language detected"],
                suggested_action=ActionType.MODIFY,
                mitigation_strategy="Add appropriate qualifiers and uncertainty indicators"
            ))
        
        return violations
    
    def _contains_overconfident_statements(self, content: str) -> bool:
        """Check for overconfident statements"""
        overconfident_patterns = [
            r'\b(?:definitely|certainly|absolutely|undoubtedly)\s+(?:will|should|must)',
            r'\b(?:always|never|all|none|every)\s+(?:patients|clients|cases)',
            r'\b(?:proven|established|confirmed)\s+(?:fact|truth|reality)'
        ]
        
        for pattern in overconfident_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False


class EthicalComplianceGuardrail(BaseGuardrail):
    """Guardrail for ensuring ethical compliance in healthcare AI"""
    
    def __init__(self):
        super().__init__(
            "Ethical Compliance",
            "Ensures AI outputs comply with healthcare ethics and professional standards"
        )
        
        # Define ethical principles
        self.ethical_principles = {
            'autonomy': ['patient choice', 'informed consent', 'decision-making'],
            'beneficence': ['patient benefit', 'do good', 'positive outcome'],
            'non_maleficence': ['do no harm', 'avoid harm', 'prevent injury'],
            'justice': ['fair treatment', 'equal access', 'equitable care']
        }
        
        # Define ethical violations
        self.ethical_violations = [
            r'\b(?:force|coerce|pressure)\s+(?:\w+\s+){0,2}?(?:patient|client)',
            r'\b(?:withhold|deny|refuse)\s+(?:information|treatment|care)',
            r'\b(?:discriminate|exclude|reject)\s+(?:based on|due to)',
            r'\b(?:experimental|unproven|untested)\s+(?:without|lacking)\s+(?:consent|approval)'
        ]
    
    def evaluate(self, content: str, context: Dict[str, Any]) -> List[GuardrailViolation]:
        violations = []
        
        # Check for ethical violations
        for pattern in self.ethical_violations:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                violations.append(GuardrailViolation(
                    guardrail_type=GuardrailType.ETHICAL_COMPLIANCE,
                    violation_type="ethical_violation",
                    description=f"Potential ethical violation detected: '{match.group()}'",
                    risk_level=RiskLevel.HIGH,
                    confidence=0.9,
                    evidence=[match.group()],
                    suggested_action=ActionType.BLOCK,
                    mitigation_strategy="Revise content to align with healthcare ethical principles"
                ))
        
        # Check for missing ethical considerations
        if self._missing_ethical_considerations(content, context):
            violations.append(GuardrailViolation(
                guardrail_type=GuardrailType.ETHICAL_COMPLIANCE,
                violation_type="missing_ethical_considerations",
                description="Content lacks appropriate ethical considerations for healthcare context",
                risk_level=RiskLevel.MEDIUM,
                confidence=0.6,
                evidence=["Ethical considerations missing"],
                suggested_action=ActionType.MODIFY,
                mitigation_strategy="Add appropriate ethical disclaimers and considerations"
            ))
        
        return violations
    
    def _missing_ethical_considerations(self, content: str, context: Dict[str, Any]) -> bool:
        """Check if content is missing ethical considerations"""
        # For high-stakes content, ensure ethical considerations are present
        if context.get('content_type') in ['recommendation', 'treatment_plan', 'diagnosis']:
            ethical_indicators = [
                'patient autonomy', 'informed consent', 'professional judgment',
                'individual circumstances', 'clinical expertise'
            ]
            
            content_lower = content.lower()
            for indicator in ethical_indicators:
                if indicator in content_lower:
                    return False
            return True
        
        return False


class TransparencyEnforcementGuardrail(BaseGuardrail):
    """Guardrail for enforcing AI transparency and explainability"""
    
    def __init__(self):
        super().__init__(
            "Transparency Enforcement",
            "Ensures AI outputs include appropriate transparency and explainability information"
        )
        
        # Define required transparency elements
        self.transparency_requirements = {
            'ai_disclosure': ['AI-generated', 'artificial intelligence', 'automated analysis'],
            'confidence_indicators': ['confidence', 'certainty', 'likelihood'],
            'limitations': ['limitation', 'constraint', 'boundary'],
            'human_oversight': ['professional judgment', 'clinical expertise', 'human review']
        }
    
    def evaluate(self, content: str, context: Dict[str, Any]) -> List[GuardrailViolation]:
        violations = []
        
        # Check for missing transparency elements
        missing_elements = self._check_transparency_elements(content, context)
        
        for element in missing_elements:
            violations.append(GuardrailViolation(
                guardrail_type=GuardrailType.TRANSPARENCY_ENFORCEMENT,
                violation_type=f"missing_{element}",
                description=f"Content lacks required transparency element: {element}",
                risk_level=RiskLevel.MEDIUM,
                confidence=0.8,
                evidence=[f"Missing {element}"],
                suggested_action=ActionType.MODIFY,
                mitigation_strategy=f"Add appropriate {element} information to ensure transparency"
            ))
        
        return violations
    
    def _check_transparency_elements(self, content: str, context: Dict[str, Any]) -> List[str]:
        """Check which transparency elements are missing"""
        missing = []
        content_lower = content.lower()
        
        # If content is empty, don't flag transparency violations
        if not content_lower.strip():
            return []
        
        # Check if this is AI-generated content that needs transparency
        if context.get('ai_generated', True):
            for element, indicators in self.transparency_requirements.items():
                if not any(indicator.lower() in content_lower for indicator in indicators):
                    missing.append(element)
        
        return missing


class AIGuardrailsService:
    """Main service for AI guardrails and responsible AI controls"""
    
    def __init__(self):
        self.guardrails: List[BaseGuardrail] = []
        self.violation_history: List[GuardrailResult] = []
        self.transparency_templates = self._load_transparency_templates()
        
        # Initialize default guardrails
        self._initialize_default_guardrails()
    
    def _initialize_default_guardrails(self) -> None:
        """Initialize default set of guardrails"""
        self.guardrails = [
            ContentSafetyGuardrail(),
            BiasDetectionGuardrail(),
            AccuracyValidationGuardrail(),
            EthicalComplianceGuardrail(),
            TransparencyEnforcementGuardrail()
        ]
        
        logger.info(f"Initialized {len(self.guardrails)} AI guardrails")
    
    def _load_transparency_templates(self) -> Dict[str, str]:
        """Load transparency statement templates"""
        return {
            'ai_disclosure': "This content was generated using artificial intelligence and should be reviewed by qualified professionals.",
            'confidence_low': "This analysis has low confidence and requires additional verification.",
            'confidence_medium': "This analysis has moderate confidence and should be validated by clinical expertise.",
            'confidence_high': "This analysis has high confidence but still requires professional judgment.",
            'limitations': "AI analysis has limitations and may not capture all relevant clinical factors.",
            'human_oversight': "Professional clinical judgment is required to validate and act upon these findings."
        }
    
    def evaluate_content(self, content: str, context: Dict[str, Any]) -> GuardrailResult:
        """Evaluate content against all applicable guardrails"""
        content_id = self._generate_content_id(content)
        all_violations = []
        
        # Run all applicable guardrails
        for guardrail in self.guardrails:
            if guardrail.is_applicable(context):
                try:
                    violations = guardrail.evaluate(content, context)
                    all_violations.extend(violations)
                    
                    if violations:
                        guardrail.violation_count += len(violations)
                        guardrail.last_triggered = datetime.now()
                        
                except Exception as e:
                    logger.error(f"Error in guardrail {guardrail.name}: {e}")
        
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
            confidence_adjustments=confidence_adjustments
        )
        
        # Store result for audit trail
        self.violation_history.append(result)
        
        logger.info(f"Guardrail evaluation complete: {len(all_violations)} violations, "
                   f"risk level: {overall_risk.value}, action: {action_taken.value}")
        
        return result
    
    def _generate_content_id(self, content: str) -> str:
        """Generate unique ID for content"""
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _calculate_overall_risk(self, violations: List[GuardrailViolation]) -> RiskLevel:
        """Calculate overall risk level from violations"""
        if not violations:
            return RiskLevel.LOW
        
        # Count violations by risk level
        risk_counts = Counter(v.risk_level for v in violations)
        
        if risk_counts[RiskLevel.CRITICAL] > 0:
            return RiskLevel.CRITICAL
        elif risk_counts[RiskLevel.HIGH] > 0:
            return RiskLevel.HIGH
        elif risk_counts[RiskLevel.MEDIUM] > 0:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _determine_action(self, violations: List[GuardrailViolation], overall_risk: RiskLevel) -> ActionType:
        """Determine action to take based on violations and risk level"""
        if overall_risk == RiskLevel.CRITICAL:
            return ActionType.BLOCK
        elif overall_risk == RiskLevel.HIGH:
            # Check if any violations require blocking
            if any(v.suggested_action == ActionType.BLOCK for v in violations):
                return ActionType.BLOCK
            else:
                return ActionType.MODIFY
        elif overall_risk == RiskLevel.MEDIUM:
            return ActionType.MODIFY
        else:
            return ActionType.ALLOW
    
    def _apply_modifications(self, content: str, violations: List[GuardrailViolation], 
                           context: Dict[str, Any]) -> Optional[str]:
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
        modified_content = self._add_transparency_statements(modified_content, violations, context)
        
        return modified_content if modified_content != content else None
    
    def _apply_specific_modification(self, content: str, violation: GuardrailViolation, 
                                   context: Dict[str, Any]) -> str:
        """Apply specific modification for a violation"""
        if violation.guardrail_type == GuardrailType.BIAS_DETECTION:
            # Apply inclusive language modifications
            for evidence in violation.evidence:
                if 'typical patient' in evidence.lower():
                    content = content.replace(evidence, 'patients')
                elif 'all women' in evidence.lower():
                    content = content.replace(evidence, 'some women')
                # Add more specific replacements as needed
        
        elif violation.guardrail_type == GuardrailType.ACCURACY_VALIDATION:
            # Add uncertainty qualifiers
            if 'definitely' in content.lower():
                content = re.sub(r'\bdefinitely\b', 'likely', content, flags=re.IGNORECASE)
            if 'always' in content.lower():
                content = re.sub(r'\balways\b', 'typically', content, flags=re.IGNORECASE)
        
        elif violation.guardrail_type == GuardrailType.CONTENT_SAFETY:
            # Apply safety modifications
            for evidence in violation.evidence:
                # Replace with safer alternatives
                content = content.replace(evidence, '[CONTENT MODIFIED FOR SAFETY]')
        
        return content
    
    def _add_transparency_statements(self, content: str, violations: List[GuardrailViolation], 
                                   context: Dict[str, Any]) -> str:
        """Add transparency statements to content"""
        transparency_additions = []
        
        # Add AI disclosure if missing
        if any(v.violation_type == 'missing_ai_disclosure' for v in violations):
            transparency_additions.append(self.transparency_templates['ai_disclosure'])
        
        # Add confidence indicators
        confidence_level = context.get('confidence_level', 'medium')
        if confidence_level in self.transparency_templates:
            transparency_additions.append(self.transparency_templates[confidence_level])
        
        # Add limitations disclosure
        if any(v.violation_type == 'missing_limitations' for v in violations):
            transparency_additions.append(self.transparency_templates['limitations'])
        
        # Add human oversight requirement
        if any(v.violation_type == 'missing_human_oversight' for v in violations):
            transparency_additions.append(self.transparency_templates['human_oversight'])
        
        # Append transparency statements
        if transparency_additions:
            transparency_section = "\n\n**AI Transparency Notice:**\n" + "\n".join(
                f"• {statement}" for statement in transparency_additions
            )
            content += transparency_section
        
        return content
    
    def _generate_transparency_notes(self, violations: List[GuardrailViolation], 
                                   context: Dict[str, Any]) -> List[str]:
        """Generate transparency notes for the evaluation"""
        notes = []
        
        if violations:
            notes.append(f"AI guardrails detected {len(violations)} potential issues")
            
            # Group violations by type
            violation_types = Counter(v.guardrail_type for v in violations)
            for guardrail_type, count in violation_types.items():
                notes.append(f"{guardrail_type.value}: {count} issues detected")
        
        # Add confidence information
        if 'confidence_level' in context:
            notes.append(f"AI confidence level: {context['confidence_level']}")
        
        # Add model information
        if 'model_name' in context:
            notes.append(f"Generated by: {context['model_name']}")
        
        return notes
    
    def _calculate_confidence_adjustments(self, violations: List[GuardrailViolation]) -> Dict[str, float]:
        """Calculate confidence adjustments based on violations"""
        adjustments: Dict[str, float] = {}
        
        # Reduce confidence based on violation types
        for violation in violations:
            if violation.guardrail_type == GuardrailType.HALLUCINATION_DETECTION:
                adjustments['hallucination_penalty'] = -0.3
            elif violation.guardrail_type == GuardrailType.ACCURACY_VALIDATION:
                adjustments['accuracy_penalty'] = -0.2
            elif violation.guardrail_type == GuardrailType.BIAS_DETECTION:
                adjustments['bias_penalty'] = -0.1
        
        return adjustments
    
    def get_guardrail_statistics(self) -> Dict[str, Any]:
        """Get statistics about guardrail performance"""
        total_evaluations = len(self.violation_history)
        total_violations = sum(len(result.violations) for result in self.violation_history)
        
        # Calculate violation rates by type
        violation_types: defaultdict[str, int] = defaultdict(int)
        for result in self.violation_history:
            for violation in result.violations:
                violation_types[violation.guardrail_type.value] += 1
        
        # Calculate risk level distribution
        risk_levels = Counter(result.overall_risk_level for result in self.violation_history)
        
        # Calculate action distribution
        actions = Counter(result.action_taken for result in self.violation_history)
        
        return {
            'total_evaluations': total_evaluations,
            'total_violations': total_violations,
            'violation_rate': total_violations / max(total_evaluations, 1),
            'violation_types': dict(violation_types),
            'risk_level_distribution': {level.value: count for level, count in risk_levels.items()},
            'action_distribution': {action.value: count for action, count in actions.items()},
            'guardrail_status': [
                {
                    'name': g.name,
                    'enabled': g.enabled,
                    'violation_count': g.violation_count,
                    'last_triggered': g.last_triggered.isoformat() if g.last_triggered else None
                }
                for g in self.guardrails
            ]
        }
    
    def enable_guardrail(self, guardrail_name: str) -> bool:
        """Enable a specific guardrail"""
        for guardrail in self.guardrails:
            if guardrail.name == guardrail_name:
                guardrail.enabled = True
                logger.info(f"Enabled guardrail: {guardrail_name}")
                return True
        return False
    
    def disable_guardrail(self, guardrail_name: str) -> bool:
        """Disable a specific guardrail"""
        for guardrail in self.guardrails:
            if guardrail.name == guardrail_name:
                guardrail.enabled = False
                logger.info(f"Disabled guardrail: {guardrail_name}")
                return True
        return False
    
    def add_custom_guardrail(self, guardrail: BaseGuardrail) -> None:
        """Add a custom guardrail"""
        self.guardrails.append(guardrail)
        logger.info(f"Added custom guardrail: {guardrail.name}")
    
    def clear_violation_history(self) -> None:
        """Clear violation history (for privacy/storage management)"""
        self.violation_history.clear()
        logger.info("Cleared guardrail violation history")
