"""
Automatic Discipline Detection for Therapy Documentation
Detects PT, OT, SLP, or multi-discipline records using pattern matching
"""

import re
from typing import List, Dict, Set
from dataclasses import dataclass


@dataclass
class DisciplineDetectionResult:
    """Result of discipline detection."""
    detected_disciplines: List[str]  # ['PT', 'OT', 'SLP']
    confidence_scores: Dict[str, float]  # {'PT': 0.85, 'OT': 0.3, 'SLP': 0.1}
    primary_discipline: str  # 'PT' or 'MULTI' if multiple
    is_multi_discipline: bool
    evidence: Dict[str, List[str]]  # Evidence found for each discipline


class DisciplineDetector:
    """Automatically detect therapy discipline from documentation."""
    
    def __init__(self):
        # PT-specific patterns
        self.pt_patterns = {
            'credentials': re.compile(r'\b(?:PT|DPT|Physical Therapist|Physical Therapy)\b', re.IGNORECASE),
            'interventions': re.compile(
                r'\b(?:therapeutic exercise|manual therapy|gait training|balance training|'
                r'strengthening|ROM|range of motion|mobilization|ambulation|transfers|'
                r'neuromuscular re-education|functional mobility)\b', 
                re.IGNORECASE
            ),
            'measurements': re.compile(
                r'\b(?:degrees?|°|strength grade|muscle grade|MMT|manual muscle test|'
                r'goniometry|ROM measurement)\b',
                re.IGNORECASE
            ),
            'equipment': re.compile(
                r'\b(?:walker|cane|crutches|parallel bars|treadmill|weights|theraband)\b',
                re.IGNORECASE
            )
        }
        
        # OT-specific patterns
        self.ot_patterns = {
            'credentials': re.compile(r'\b(?:OT|OTR|COTA|Occupational Therapist|Occupational Therapy)\b', re.IGNORECASE),
            'interventions': re.compile(
                r'\b(?:ADL|activities of daily living|fine motor|gross motor|sensory|'
                r'self-care|dressing|feeding|grooming|bathing|toileting|'
                r'adaptive equipment|splinting|hand therapy|cognitive)\b',
                re.IGNORECASE
            ),
            'assessments': re.compile(
                r'\b(?:FIM|functional independence measure|COPM|Canadian Occupational|'
                r'sensory processing|visual motor|perceptual)\b',
                re.IGNORECASE
            ),
            'focus_areas': re.compile(
                r'\b(?:independence|self-care|functional independence|home management|'
                r'work activities|leisure activities)\b',
                re.IGNORECASE
            )
        }
        
        # SLP-specific patterns
        self.slp_patterns = {
            'credentials': re.compile(r'\b(?:SLP|CCC-SLP|Speech Therapist|Speech-Language Pathologist|Speech Therapy)\b', re.IGNORECASE),
            'interventions': re.compile(
                r'\b(?:aphasia|dysarthria|apraxia|dysphagia|swallowing|articulation|'
                r'phonology|fluency|stuttering|voice|resonance|language|'
                r'cognitive-communication|pragmatics)\b',
                re.IGNORECASE
            ),
            'assessments': re.compile(
                r'\b(?:FEES|fiberoptic endoscopic evaluation|modified barium swallow|'
                r'MBS|videofluoroscopy|VFSS|oral mechanism exam|OME)\b',
                re.IGNORECASE
            ),
            'techniques': re.compile(
                r'\b(?:cue|cues|cueing|strategy|strategies|compensatory|'
                r'supraglottic swallow|chin tuck|head turn|effortful swallow)\b',
                re.IGNORECASE
            )
        }
        
        # Threshold for detection
        self.confidence_threshold = 0.3  # 30% confidence to include discipline
        self.primary_threshold = 0.6  # 60% confidence to be primary
    
    def detect_disciplines(self, text: str) -> DisciplineDetectionResult:
        """
        Detect which therapy disciplines are present in the documentation.
        
        Args:
            text: Documentation text to analyze
            
        Returns:
            DisciplineDetectionResult with detected disciplines and confidence
        """
        text_lower = text.lower()
        
        # Calculate scores for each discipline
        pt_score, pt_evidence = self._calculate_discipline_score(text, self.pt_patterns)
        ot_score, ot_evidence = self._calculate_discipline_score(text, self.ot_patterns)
        slp_score, slp_evidence = self._calculate_discipline_score(text, self.slp_patterns)
        
        confidence_scores = {
            'PT': pt_score,
            'OT': ot_score,
            'SLP': slp_score
        }
        
        evidence = {
            'PT': pt_evidence,
            'OT': ot_evidence,
            'SLP': slp_evidence
        }
        
        # Determine detected disciplines
        detected = []
        for discipline, score in confidence_scores.items():
            if score >= self.confidence_threshold:
                detected.append(discipline)
        
        # Determine primary discipline
        if len(detected) == 0:
            primary = 'UNKNOWN'
            is_multi = False
        elif len(detected) == 1:
            primary = detected[0]
            is_multi = False
        else:
            # Multiple disciplines detected
            is_multi = True
            # Primary is the one with highest score above primary threshold
            max_score = max(confidence_scores.values())
            if max_score >= self.primary_threshold:
                primary = max(confidence_scores, key=confidence_scores.get)
            else:
                primary = 'MULTI'
        
        return DisciplineDetectionResult(
            detected_disciplines=detected,
            confidence_scores=confidence_scores,
            primary_discipline=primary,
            is_multi_discipline=is_multi,
            evidence=evidence
        )
    
    def _calculate_discipline_score(self, text: str, patterns: Dict[str, re.Pattern]) -> tuple[float, List[str]]:
        """
        Calculate confidence score for a discipline based on pattern matches.
        
        Returns:
            Tuple of (score, evidence_list)
        """
        matches = 0
        total_patterns = len(patterns)
        evidence = []
        
        for pattern_name, pattern in patterns.items():
            found = pattern.findall(text)
            if found:
                matches += 1
                # Add first few matches as evidence
                evidence.extend(found[:3])
        
        # Score is percentage of patterns matched
        score = matches / total_patterns if total_patterns > 0 else 0.0
        
        return score, evidence
    
    def get_discipline_summary(self, result: DisciplineDetectionResult) -> str:
        """Get a human-readable summary of detection results."""
        if result.primary_discipline == 'UNKNOWN':
            return "Unable to determine discipline - no clear indicators found"
        
        if result.is_multi_discipline:
            disciplines = ' + '.join(result.detected_disciplines)
            return f"Multi-discipline record: {disciplines}"
        else:
            confidence = result.confidence_scores[result.primary_discipline]
            return f"{result.primary_discipline} record (confidence: {confidence:.0%})"
    
    def get_detailed_report(self, result: DisciplineDetectionResult) -> str:
        """Get detailed report with evidence."""
        lines = []
        lines.append("=== Discipline Detection Report ===\n")
        
        if result.is_multi_discipline:
            lines.append(f"Type: Multi-Discipline Record")
            lines.append(f"Disciplines: {', '.join(result.detected_disciplines)}\n")
        else:
            lines.append(f"Primary Discipline: {result.primary_discipline}\n")
        
        lines.append("Confidence Scores:")
        for discipline in ['PT', 'OT', 'SLP']:
            score = result.confidence_scores[discipline]
            status = "✓ Detected" if discipline in result.detected_disciplines else "✗ Not detected"
            lines.append(f"  {discipline}: {score:.0%} {status}")
        
        lines.append("\nEvidence Found:")
        for discipline in result.detected_disciplines:
            evidence = result.evidence[discipline]
            if evidence:
                lines.append(f"\n{discipline}:")
                for item in evidence[:5]:  # Show first 5 pieces of evidence
                    lines.append(f"  • {item}")
        
        return '\n'.join(lines)


class PatientRecordAnalyzer:
    """Analyze complete patient records across multiple disciplines."""
    
    def __init__(self):
        self.detector = DisciplineDetector()
    
    def analyze_patient_record(self, documents: List[Dict[str, str]]) -> Dict:
        """
        Analyze a complete patient record with multiple documents.
        
        Args:
            documents: List of dicts with 'text' and optional 'date', 'type' keys
            
        Returns:
            Comprehensive analysis including:
            - Overall discipline breakdown
            - Timeline of services
            - Multi-discipline coordination
            - Analytics by discipline
        """
        results = []
        discipline_counts = {'PT': 0, 'OT': 0, 'SLP': 0}
        multi_discipline_count = 0
        
        # Analyze each document
        for doc in documents:
            text = doc.get('text', '')
            detection = self.detector.detect_disciplines(text)
            
            results.append({
                'document': doc,
                'detection': detection
            })
            
            # Count disciplines
            for discipline in detection.detected_disciplines:
                discipline_counts[discipline] += 1
            
            if detection.is_multi_discipline:
                multi_discipline_count += 1
        
        # Calculate overall statistics
        total_docs = len(documents)
        
        return {
            'total_documents': total_docs,
            'discipline_breakdown': discipline_counts,
            'multi_discipline_documents': multi_discipline_count,
            'pt_percentage': (discipline_counts['PT'] / total_docs * 100) if total_docs > 0 else 0,
            'ot_percentage': (discipline_counts['OT'] / total_docs * 100) if total_docs > 0 else 0,
            'slp_percentage': (discipline_counts['SLP'] / total_docs * 100) if total_docs > 0 else 0,
            'is_comprehensive_care': len([d for d in discipline_counts.values() if d > 0]) >= 2,
            'document_results': results
        }
    
    def get_discipline_specific_analytics(self, patient_analysis: Dict, discipline: str) -> Dict:
        """Get analytics for a specific discipline within patient record."""
        discipline_docs = [
            r for r in patient_analysis['document_results']
            if discipline in r['detection'].detected_disciplines
        ]
        
        return {
            'discipline': discipline,
            'document_count': len(discipline_docs),
            'percentage_of_total': (len(discipline_docs) / patient_analysis['total_documents'] * 100) 
                if patient_analysis['total_documents'] > 0 else 0,
            'documents': discipline_docs
        }
    
    def get_multi_discipline_coordination_report(self, patient_analysis: Dict) -> str:
        """Generate report on multi-discipline coordination."""
        lines = []
        lines.append("=== Multi-Discipline Coordination Report ===\n")
        
        total = patient_analysis['total_documents']
        breakdown = patient_analysis['discipline_breakdown']
        
        lines.append(f"Total Documents: {total}")
        lines.append(f"Multi-Discipline Documents: {patient_analysis['multi_discipline_documents']}\n")
        
        lines.append("Discipline Distribution:")
        lines.append(f"  PT: {breakdown['PT']} documents ({patient_analysis['pt_percentage']:.1f}%)")
        lines.append(f"  OT: {breakdown['OT']} documents ({patient_analysis['ot_percentage']:.1f}%)")
        lines.append(f"  SLP: {breakdown['SLP']} documents ({patient_analysis['slp_percentage']:.1f}%)\n")
        
        if patient_analysis['is_comprehensive_care']:
            lines.append("✓ Comprehensive multi-discipline care detected")
            active_disciplines = [d for d, count in breakdown.items() if count > 0]
            lines.append(f"  Active disciplines: {', '.join(active_disciplines)}")
        else:
            lines.append("Single discipline care")
        
        return '\n'.join(lines)
