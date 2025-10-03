"""Mock Analysis Service for testing and development."""

import asyncio
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger(__name__)


class MockAnalysisService:
    """Mock implementation of AnalysisService for testing and development."""
    
    def __init__(self):
        """Initialize mock analysis service."""
        self.logger = logger
        self.is_initialized = True
        
    async def analyze_document(
        self,
        document_text: str,
        discipline: str = "pt",
        rubric_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock document analysis that returns realistic test results."""
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Generate mock findings based on discipline
        findings = self._generate_mock_findings(discipline, document_text)
        
        # Calculate mock compliance score
        compliance_score = self._calculate_mock_score(findings)
        
        return {
            "compliance_score": compliance_score,
            "discipline": discipline,
            "findings": findings,
            "total_financial_impact": sum(f.get("financial_impact", 0) for f in findings),
            "analysis_metadata": {
                "service_type": "mock",
                "rubric_applied": rubric_name or f"{discipline.upper()} Mock Rubric",
                "processing_time": 0.5,
                "confidence": 0.85
            },
            "recommendations": self._generate_mock_recommendations(discipline),
            "document_classification": {
                "type": "Progress Note",
                "confidence": 0.9
            }
        }
    
    def _generate_mock_findings(self, discipline: str, text: str) -> List[Dict[str, Any]]:
        """Generate realistic mock findings based on discipline."""
        findings = []
        text_lower = text.lower()
        
        # Common findings across disciplines
        if "signature" not in text_lower and "signed" not in text_lower:
            findings.append({
                "rule_id": "signature_missing",
                "title": "Provider signature may be missing",
                "severity": "HIGH",
                "financial_impact": 50,
                "suggestion": "Ensure all notes are signed and dated by the treating therapist with credentials.",
                "evidence": "No clear signature found in documentation",
                "confidence": 0.8
            })
        
        if "goal" not in text_lower:
            findings.append({
                "rule_id": "goals_missing",
                "title": "Treatment goals not clearly documented",
                "severity": "MEDIUM", 
                "financial_impact": 40,
                "suggestion": "Document specific, measurable treatment goals with timeframes.",
                "evidence": "No clear treatment goals identified",
                "confidence": 0.7
            })
        
        # Discipline-specific findings
        if discipline.lower() == "pt":
            if "functional" not in text_lower:
                findings.append({
                    "rule_id": "functional_outcomes",
                    "title": "Functional outcomes not documented",
                    "severity": "MEDIUM",
                    "financial_impact": 35,
                    "suggestion": "Link treatment interventions to functional outcomes and ADL improvements.",
                    "evidence": "Missing functional outcome documentation",
                    "confidence": 0.75
                })
        
        elif discipline.lower() == "ot":
            if "adl" not in text_lower and "activities of daily living" not in text_lower:
                findings.append({
                    "rule_id": "adl_focus",
                    "title": "ADL focus not clearly documented",
                    "severity": "MEDIUM",
                    "financial_impact": 30,
                    "suggestion": "Document how interventions address activities of daily living.",
                    "evidence": "No clear ADL focus identified",
                    "confidence": 0.8
                })
        
        elif discipline.lower() == "slp":
            if "communication" not in text_lower and "speech" not in text_lower:
                findings.append({
                    "rule_id": "communication_goals",
                    "title": "Communication goals not specified",
                    "severity": "MEDIUM",
                    "financial_impact": 45,
                    "suggestion": "Specify communication or swallowing goals with measurable criteria.",
                    "evidence": "No clear communication goals found",
                    "confidence": 0.85
                })
        
        return findings
    
    def _calculate_mock_score(self, findings: List[Dict[str, Any]]) -> int:
        """Calculate mock compliance score based on findings."""
        if not findings:
            return 95
        
        # Start with perfect score and deduct based on severity
        score = 100
        for finding in findings:
            severity = finding.get("severity", "LOW")
            if severity == "HIGH":
                score -= 15
            elif severity == "MEDIUM":
                score -= 10
            else:
                score -= 5
        
        return max(score, 0)
    
    def _generate_mock_recommendations(self, discipline: str) -> List[str]:
        """Generate mock recommendations based on discipline."""
        base_recommendations = [
            "Ensure all documentation is signed and dated",
            "Use specific, measurable language in goal setting",
            "Document medical necessity clearly"
        ]
        
        discipline_specific = {
            "pt": [
                "Link interventions to functional outcomes",
                "Document objective measurements (ROM, strength, etc.)",
                "Include safety considerations and precautions"
            ],
            "ot": [
                "Focus on ADL and IADL improvements", 
                "Document cognitive and perceptual factors",
                "Include adaptive equipment recommendations"
            ],
            "slp": [
                "Specify communication modalities addressed",
                "Document swallowing safety if applicable",
                "Include family/caregiver education"
            ]
        }
        
        return base_recommendations + discipline_specific.get(discipline.lower(), [])
    
    def is_ready(self) -> bool:
        """Check if the mock service is ready."""
        return self.is_initialized
    
    async def initialize(self):
        """Initialize the mock service (no-op for mock)."""
        self.is_initialized = True
        logger.info("Mock Analysis Service initialized")
    
    async def shutdown(self):
        """Shutdown the mock service (no-op for mock)."""
        logger.info("Mock Analysis Service shutdown")