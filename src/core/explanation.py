import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExplanationContext:
    """Context information for generating explanations."""
    document_type: Optional[str] = None
    discipline: Optional[str] = None  # PT, OT, SLP
    rubric_name: Optional[str] = None
    analysis_confidence: Optional[float] = None


class ExplanationEngine:
    """
    Enhanced explanation engine for clinical compliance analysis.
    
    Provides contextual explanations, regulatory citations, and actionable
    recommendations for compliance findings in therapy documentation.
    """
    
    def __init__(self):
        self.regulatory_citations = {
            "medicare": "Medicare Guidelines (CMS)",
            "pt": "APTA Practice Guidelines",
            "ot": "AOTA Standards of Practice", 
            "slp": "ASHA Code of Ethics"
        }
    
    def add_explanations(
        self, 
        analysis_result: Dict[str, Any], 
        full_document_text: str,
        context: Optional[ExplanationContext] = None
    ) -> Dict[str, Any]:
        """
        Add comprehensive explanations to analysis findings.
        
        Args:
            analysis_result: Raw analysis results with findings
            full_document_text: Complete source document text
            context: Additional context for explanation generation
            
        Returns:
            Enhanced analysis result with explanations and recommendations
        """
        if "findings" not in analysis_result or not isinstance(
            analysis_result.get("findings"), list
        ):
            logger.warning("No findings found in analysis result")
            return analysis_result
            
        context = context or ExplanationContext()
        
        for finding in analysis_result["findings"]:
            self._enhance_finding(finding, full_document_text, context)
            
        # Add overall analysis metadata
        analysis_result["explanation_metadata"] = {
            "document_type": context.document_type,
            "discipline": context.discipline,
            "rubric_applied": context.rubric_name,
            "explanation_version": "2.0"
        }
        
        return analysis_result
    
    def _enhance_finding(
        self, 
        finding: Dict[str, Any], 
        full_document_text: str,
        context: ExplanationContext
    ) -> None:
        """Enhance a single finding with explanations and context."""
        problematic_text = finding.get("text", "")
        
        # Add context snippet with improved window sizing
        if problematic_text:
            finding["context_snippet"] = self._get_context_snippet(
                problematic_text, full_document_text
            )
            
        # Add regulatory explanation
        finding["regulatory_explanation"] = self._generate_regulatory_explanation(
            finding, context
        )
        
        # Add actionable recommendation
        finding["recommendation"] = self._generate_recommendation(finding, context)
        
        # Add confidence with proper calculation (remove random generation)
        if "confidence" not in finding:
            finding["confidence"] = self._calculate_confidence(finding, context)
            
        # Add severity assessment
        finding["severity"] = self._assess_severity(finding)
        
        # Add citation information
        finding["citation"] = self._get_regulatory_citation(finding, context)
    
    def _generate_regulatory_explanation(
        self, 
        finding: Dict[str, Any], 
        context: ExplanationContext
    ) -> str:
        """Generate explanation of why this finding violates regulations."""
        issue_type = finding.get("issue_type", "compliance")
        discipline = context.discipline or "therapy"
        
        explanations = {
            "missing_frequency": f"Medicare requires specific frequency documentation for {discipline} services to justify medical necessity.",
            "missing_goals": f"Functional goals must be measurable and time-bound per {discipline} practice standards.",
            "missing_progress": f"Progress documentation is required to demonstrate skilled {discipline} intervention effectiveness.",
            "missing_plan": f"Treatment plan modifications must be documented to show clinical reasoning in {discipline} care."
        }
        
        return explanations.get(
            issue_type, 
            f"This finding may impact compliance with Medicare and professional {discipline} documentation standards."
        )
    
    def _generate_recommendation(
        self, 
        finding: Dict[str, Any], 
        context: ExplanationContext
    ) -> str:
        """Generate specific, actionable recommendation for the finding."""
        issue_type = finding.get("issue_type", "compliance")
        discipline = context.discipline or "therapy"
        
        # Base recommendations by issue type
        recommendations = {
            "missing_frequency": f"Add specific frequency (e.g., '3x/week for 4 weeks') with clinical justification for {discipline} services.",
            "missing_goals": f"Include SMART goals with measurable outcomes and target dates appropriate for {discipline} intervention.",
            "missing_progress": f"Document specific functional improvements with objective measurements showing {discipline} effectiveness.",
            "missing_plan": f"Clearly state treatment plan modifications with clinical reasoning for {discipline} care."
        }
        
        # Discipline-specific enhancements
        if context.discipline:
            if context.discipline.lower() == "pt":
                recommendations["missing_goals"] += " Focus on functional mobility and strength outcomes."
            elif context.discipline.lower() == "ot":
                recommendations["missing_goals"] += " Emphasize ADL independence and occupational performance."
            elif context.discipline.lower() == "slp":
                recommendations["missing_goals"] += " Target communication and swallowing function improvements."
        
        return recommendations.get(
            issue_type,
            f"Review documentation against applicable {discipline} compliance standards and add missing elements."
        )
    
    def _calculate_confidence(
        self, 
        finding: Dict[str, Any], 
        context: ExplanationContext
    ) -> float:
        """Calculate confidence score based on finding characteristics."""
        base_confidence = 0.85
        
        # Adjust based on text length and specificity
        text_length = len(finding.get("text", ""))
        if text_length > 50:
            base_confidence += 0.05
        elif text_length < 20:
            base_confidence -= 0.10
            
        # Adjust based on issue type specificity
        issue_type = finding.get("issue_type")
        if issue_type in ["missing_frequency", "missing_goals"]:
            base_confidence += 0.08  # High confidence for clear violations
        
        # Adjust based on context availability
        if context.document_type:
            base_confidence += 0.03
        if context.discipline:
            base_confidence += 0.02
        if context.rubric_name:
            base_confidence += 0.02
            
        return round(min(max(base_confidence, 0.60), 0.98), 2)
    
    def _assess_severity(self, finding: Dict[str, Any]) -> str:
        """Assess the severity level of a compliance finding."""
        issue_type = finding.get("issue_type", "")
        confidence = finding.get("confidence", 0.0)
        
        # High severity issues
        if issue_type in ["missing_medical_necessity", "missing_physician_orders"]:
            return "High"
        
        # Medium severity with high confidence
        if confidence > 0.90 and issue_type in ["missing_frequency", "missing_goals"]:
            return "Medium"
            
        # Low severity for less critical or uncertain findings
        if confidence < 0.80:
            return "Low"
            
        return "Medium"
    
    def _get_regulatory_citation(
        self, 
        finding: Dict[str, Any], 
        context: ExplanationContext
    ) -> str:
        """Get appropriate regulatory citation for the finding."""
        # Use finding to determine citation type if needed
        issue_type = finding.get("issue_type", "")
        discipline = context.discipline or "general"
        
        # Special citations for specific issue types
        if "medical_necessity" in issue_type:
            return "Medicare Guidelines (42 CFR 424.5)"
        
        if discipline.lower() in self.regulatory_citations:
            return self.regulatory_citations[discipline.lower()]
        
        return self.regulatory_citations["medicare"]

    @staticmethod
    def _get_context_snippet(
        text_to_find: str, full_text: str, window: int = 50
    ) -> str:
        """
        Extract context snippet around problematic text for better understanding.
        
        Args:
            text_to_find: The problematic text to locate
            full_text: Complete document text
            window: Number of characters to include before/after the text
            
        Returns:
            Context snippet with the problematic text highlighted
        """
        try:
            if not text_to_find or not full_text:
                return text_to_find or ""
                
            start_index = full_text.find(text_to_find)
            if start_index == -1:
                # Try case-insensitive search
                lower_full = full_text.lower()
                lower_find = text_to_find.lower()
                start_index = lower_full.find(lower_find)
                if start_index == -1:
                    return text_to_find
            
            # Find word boundaries for better context
            context_start = max(0, start_index - window)
            context_end = min(len(full_text), start_index + len(text_to_find) + window)
            
            # Adjust to word boundaries if possible
            while context_start > 0 and full_text[context_start] not in ' \n\t':
                context_start -= 1
            while context_end < len(full_text) and full_text[context_end] not in ' \n\t':
                context_end += 1
                
            context = full_text[context_start:context_end].strip()
            
            # Add ellipsis if we're not at document boundaries
            if context_start > 0:
                context = "..." + context
            if context_end < len(full_text):
                context = context + "..."
                
            return context
            
        except (ValueError, IndexError, AttributeError) as e:
            logger.warning("Error extracting context snippet: %s", e)
            return text_to_find
