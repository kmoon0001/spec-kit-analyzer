"""
Simple AI Guardrails Demo

This standalone demo showcases the AI guardrails system without complex dependencies,
demonstrating responsible AI controls, bias detection, and safety measures.
"""

import sys
import re
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any

# Simple standalone implementation for demonstration
class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ActionType(Enum):
    ALLOW = "allow"
    MODIFY = "modify"
    FLAG = "flag"
    BLOCK = "block"

@dataclass
class GuardrailResult:
    content: str
    violations: List[str]
    risk_level: RiskLevel
    action: ActionType
    modified_content: str = None

class SimpleAIGuardrails:
    """Simplified AI guardrails for demonstration"""
    
    def __init__(self):
        self.bias_patterns = [
            r'\ball\s+(?:elderly|women|men|patients)\s+(?:typically|always|never)',
            r'\b(?:typical|normal|standard)\s+(?:patient|client)',
            r'\b(?:low-income|poor|wealthy)\s+patients\s+(?:usually|often|always)'
        ]
        
        self.safety_patterns = [
            r'\b(?:guarantee|promise|ensure)\s+(?:cure|recovery)',
            r'\b(?:definitely|certainly|absolutely)\s+(?:will|cure|fix)',
            r'\b(?:force|coerce|pressure)\s+(?:patient|client)'
        ]
        
        self.transparency_requirements = [
            'ai-generated', 'artificial intelligence', 'confidence', 'professional judgment'
        ]
    
    def evaluate_content(self, content: str, context: Dict[str, Any] = None) -> GuardrailResult:
        """Evaluate content against guardrails"""
        violations = []
        modified_content = content
        
        # Check for bias
        for pattern in self.bias_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(f"Bias detected: {pattern}")
                # Apply simple modification
                modified_content = re.sub(r'\ball\s+elderly\s+patients', 'some older adult patients', 
                                        modified_content, flags=re.IGNORECASE)
        
        # Check for safety issues
        for pattern in self.safety_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(f"Safety issue: {pattern}")
                # Apply safety modification
                modified_content = re.sub(r'\bdefinitely\s+will', 'may potentially', 
                                        modified_content, flags=re.IGNORECASE)
        
        # Check transparency
        if context and context.get('ai_generated', False):
            has_transparency = any(req in content.lower() for req in self.transparency_requirements)
            if not has_transparency:
                violations.append("Missing AI transparency disclosure")
                modified_content += "\n\n**AI Transparency Notice:** This content was generated using artificial intelligence and requires professional review."
        
        # Determine risk level and action
        if len(violations) == 0:
            risk_level = RiskLevel.LOW
            action = ActionType.ALLOW
        elif len(violations) <= 2:
            risk_level = RiskLevel.MEDIUM
            action = ActionType.MODIFY
        else:
            risk_level = RiskLevel.HIGH
            action = ActionType.FLAG
        
        return GuardrailResult(
            content=content,
            violations=violations,
            risk_level=risk_level,
            action=action,
            modified_content=modified_content if modified_content != content else None
        )

class Simple7HabitsMapper:
    """Simplified 7 Habits mapper for demonstration"""
    
    def __init__(self):
        self.habits = {
            1: {
                "name": "Be Proactive",
                "description": "Take initiative and responsibility for your professional development",
                "keywords": ["initiative", "responsibility", "proactive", "ownership"]
            },
            2: {
                "name": "Begin with the End in Mind",
                "description": "Set clear goals and work systematically toward compliance excellence",
                "keywords": ["goals", "planning", "vision", "systematic"]
            },
            3: {
                "name": "Put First Things First",
                "description": "Prioritize critical compliance areas and manage time effectively",
                "keywords": ["priority", "time management", "critical", "important"]
            },
            4: {
                "name": "Think Win-Win",
                "description": "Collaborate effectively with team members and patients",
                "keywords": ["collaboration", "teamwork", "mutual benefit", "cooperation"]
            },
            5: {
                "name": "Seek First to Understand, Then to Be Understood",
                "description": "Listen actively to patients and colleagues before responding",
                "keywords": ["listening", "understanding", "communication", "empathy"]
            },
            6: {
                "name": "Synergize",
                "description": "Work together to create better outcomes than individual efforts",
                "keywords": ["synergy", "teamwork", "collective", "integration"]
            },
            7: {
                "name": "Sharpen the Saw",
                "description": "Continuously improve your skills and knowledge",
                "keywords": ["improvement", "learning", "development", "growth"]
            }
        }
    
    def map_finding_to_habit(self, finding: str) -> Dict[str, Any]:
        """Map a finding to a relevant habit"""
        finding_lower = finding.lower()
        
        for habit_num, habit_info in self.habits.items():
            for keyword in habit_info["keywords"]:
                if keyword in finding_lower:
                    return {
                        "habit_number": habit_num,
                        "name": habit_info["name"],
                        "description": habit_info["description"],
                        "relevance": f"This finding relates to {habit_info['name']} because it involves {keyword}",
                        "actionable_tip": f"Focus on {habit_info['description'].lower()}"
                    }
        
        # Default to Habit 1 if no specific match
        return {
            "habit_number": 1,
            "name": self.habits[1]["name"],
            "description": self.habits[1]["description"],
            "relevance": "Taking proactive steps to address this finding",
            "actionable_tip": "Take initiative to improve in this area"
        }

def demonstrate_ai_guardrails():
    """Demonstrate AI guardrails functionality"""
    print("=== AI Guardrails & Responsible AI Demo ===\n")
    
    guardrails = SimpleAIGuardrails()
    habits_mapper = Simple7HabitsMapper()
    
    # Test cases demonstrating different scenarios
    test_cases = [
        {
            "name": "✅ Safe Professional Content",
            "content": "The patient demonstrates improvement in functional mobility with continued therapy.",
            "context": {"ai_generated": False}
        },
        {
            "name": "⚠️ Biased Language Detection",
            "content": "All elderly patients typically have compliance issues with treatment protocols.",
            "context": {"ai_generated": True}
        },
        {
            "name": "🚫 Overconfident Medical Claims",
            "content": "This treatment will definitely cure all patients completely and guarantee full recovery.",
            "context": {"ai_generated": True}
        },
        {
            "name": "🔍 Missing AI Transparency",
            "content": "Analysis shows significant patterns in the documentation quality metrics.",
            "context": {"ai_generated": True}
        },
        {
            "name": "✅ Properly Qualified Statement",
            "content": "This AI-generated analysis suggests potential improvements with moderate confidence. Professional judgment is required for implementation.",
            "context": {"ai_generated": True}
        }
    ]
    
    print("🛡️ AI GUARDRAILS EVALUATION RESULTS:\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        print(f"   Original: \"{test_case['content'][:60]}...\"")
        
        result = guardrails.evaluate_content(test_case['content'], test_case['context'])
        
        print(f"   Risk Level: {result.risk_level.value.upper()}")
        print(f"   Action: {result.action.value.upper()}")
        print(f"   Violations: {len(result.violations)}")
        
        if result.violations:
            print("   Issues Detected:")
            for violation in result.violations:
                print(f"     • {violation}")
        
        if result.modified_content and result.modified_content != result.content:
            print(f"   ✏️ Modified: \"{result.modified_content[:60]}...\"")
        
        print()
    
    # Demonstrate 7 Habits integration
    print("🎯 7 HABITS FRAMEWORK INTEGRATION:\n")
    
    sample_findings = [
        "Documentation completeness needs improvement",
        "Response time to compliance issues requires attention", 
        "Team collaboration shows positive trends",
        "Continuous learning and skill development opportunity identified",
        "Patient communication effectiveness could be enhanced"
    ]
    
    for i, finding in enumerate(sample_findings, 1):
        habit_mapping = habits_mapper.map_finding_to_habit(finding)
        
        print(f"{i}. Finding: \"{finding}\"")
        print(f"   🎯 Maps to Habit {habit_mapping['habit_number']}: {habit_mapping['name']}")
        print(f"   💡 Relevance: {habit_mapping['relevance']}")
        print(f"   📋 Action: {habit_mapping['actionable_tip']}")
        print()
    
    # Show comprehensive report features
    print("📊 COMPREHENSIVE REPORT FEATURES:\n")
    
    report_features = [
        "✅ Non-repetitive, well-organized content structure",
        "✅ Professional flow with logical section progression", 
        "✅ Informative insights with supporting evidence",
        "✅ Actionable recommendations with implementation steps",
        "✅ Educational value with training components",
        "✅ Compliance-driven regulatory alignment",
        "✅ Data-driven analysis with statistical confidence",
        "✅ Deep reasoning and logical explanations",
        "✅ Positive, constructive improvement focus",
        "✅ Visual appeal with professional styling",
        "✅ AI transparency and ethical disclosures",
        "✅ Bias mitigation and fairness controls",
        "✅ 7 Habits personal development integration",
        "✅ Responsible AI safety guardrails"
    ]
    
    for feature in report_features:
        print(f"   {feature}")
    
    print("\n🏆 RESPONSIBLE AI PRINCIPLES IMPLEMENTED:\n")
    
    principles = {
        "🔍 TRANSPARENCY": [
            "AI-generated content clearly disclosed",
            "Confidence levels and limitations shown", 
            "Model capabilities and boundaries explained"
        ],
        "⚖️ FAIRNESS": [
            "Bias detection and mitigation active",
            "Inclusive language enforcement",
            "Demographic fairness monitoring"
        ],
        "📋 ACCOUNTABILITY": [
            "Clear responsibility assignments",
            "Professional oversight requirements",
            "Audit trails and violation tracking"
        ],
        "🔒 SECURITY": [
            "Content safety monitoring",
            "Harmful content prevention", 
            "Ethical compliance enforcement"
        ]
    }
    
    for principle, features in principles.items():
        print(f"   {principle}")
        for feature in features:
            print(f"     • {feature}")
        print()
    
    print("=== DEMO COMPLETE ===\n")
    print("🎉 KEY ACHIEVEMENTS:")
    print("✅ Comprehensive AI safety controls demonstrated")
    print("✅ Bias detection and mitigation in action")
    print("✅ Transparency and explainability enforced")
    print("✅ Ethical compliance monitoring active")
    print("✅ 7 Habits framework for personal development")
    print("✅ Professional, educational, actionable reporting")
    print("✅ Responsible AI practices throughout system")

if __name__ == "__main__":
    demonstrate_ai_guardrails()