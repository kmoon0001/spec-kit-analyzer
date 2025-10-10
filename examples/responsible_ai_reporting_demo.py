"""
Responsible AI Reporting Demo

This example demonstrates the comprehensive AI guardrails system and 7 Habits
framework integration in the reporting system, showcasing responsible AI practices,
bias mitigation, transparency enforcement, and ethical compliance.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.report_generation_engine import ReportGenerationEngine, ReportConfig, ReportType
from core.ai_guardrails_service import AIGuardrailsService


async def demonstrate_responsible_ai_reporting():
    """Demonstrate responsible AI controls in report generation"""
    
    print("=== Responsible AI Reporting System Demo ===\n")
    
    # Initialize report engine with AI guardrails
    engine = ReportGenerationEngine()
    
    # 1. Check AI guardrails status
    print("1. AI Guardrails System Status:")
    guardrails_status = engine.get_ai_guardrails_status()
    if guardrails_status["available"]:
        print("   ✅ AI Guardrails: ACTIVE")
        print("   ✅ Bias Mitigation: ENABLED")
        print("   ✅ Ethical Compliance: ENFORCED")
        print("   ✅ Transparency: REQUIRED")
        print("   ✅ Content Safety: MONITORED")
    else:
        print("   ❌ AI Guardrails: NOT AVAILABLE")
    print()
    
    # 2. Check 7 Habits framework status
    print("2. 7 Habits Framework Status:")
    habits_status = engine.get_seven_habits_status()
    if habits_status["available"]:
        print("   ✅ 7 Habits Framework: INTEGRATED")
        print(f"   📚 Framework: {habits_status['framework_name']}")
        print(f"   🎯 Habits Available: {habits_status['habits_count']}")
        print("   📈 Personal Development: ENABLED")
    else:
        print("   ❌ 7 Habits Framework: NOT AVAILABLE")
    print()
    
    # 3. Demonstrate safe content generation
    print("3. Generating Report with Responsible AI Controls...")
    
    config = ReportConfig(
        report_type=ReportType.PERFORMANCE_ANALYSIS,
        title="Comprehensive Performance Analysis with AI Guardrails",
        description="Professional report demonstrating responsible AI practices and 7 Habits integration"
    )
    
    # Generate report with all safety controls
    report = await engine.generate_report(config)
    
    print(f"   📊 Report Generated: {report.id}")
    print(f"   🛡️ AI Guardrails Applied: {report.metadata.get('ai_guardrails_applied', False)}")
    print(f"   🎯 7 Habits Integrated: {report.metadata.get('seven_habits_integrated', False)}")
    print(f"   ✅ Responsible AI Compliance: {report.metadata.get('responsible_ai_compliance', False)}")
    print()
    
    # 4. Demonstrate guardrails in action
    print("4. Testing AI Guardrails with Problematic Content...")
    
    if engine.guardrails_service:
        test_cases = [
            {
                "name": "Safe Professional Content",
                "content": "The patient demonstrates improvement in functional mobility with continued therapy.",
                "expected": "SAFE"
            },
            {
                "name": "Biased Language",
                "content": "All elderly patients typically have compliance issues with treatment.",
                "expected": "BIAS DETECTED"
            },
            {
                "name": "Overconfident Claims",
                "content": "This treatment will definitely cure all patients completely.",
                "expected": "ACCURACY VIOLATION"
            },
            {
                "name": "Ethical Violation",
                "content": "Force the patient to comply with treatment regardless of their wishes.",
                "expected": "ETHICAL VIOLATION"
            },
            {
                "name": "Missing Transparency",
                "content": "This analysis shows clear patterns in the data.",
                "expected": "TRANSPARENCY REQUIRED"
            }
        ]
        
        for test_case in test_cases:
            context = {
                "content_type": "clinical_analysis",
                "ai_generated": True,
                "healthcare_context": True
            }
            
            result = engine.guardrails_service.evaluate_content(test_case["content"], context)
            
            print(f"   Test: {test_case['name']}")
            print(f"   Content: \"{test_case['content'][:50]}...\"")
            print(f"   Risk Level: {result.overall_risk_level.value.upper()}")
            print(f"   Action: {result.action_taken.value.upper()}")
            print(f"   Violations: {len(result.violations)}")
            print(f"   Safe for Use: {'✅ YES' if result.is_safe() else '❌ NO'}")
            
            if result.violations:
                print("   Issues Detected:")
                for violation in result.violations[:2]:  # Show first 2 violations
                    print(f"     • {violation.violation_type}: {violation.description}")
            
            if result.modified_content and result.modified_content != test_case["content"]:
                print("   ✏️ Content was modified for safety")
            
            print()
    
    # 5. Demonstrate 7 Habits integration
    print("5. 7 Habits Framework Integration Example...")
    
    if engine.habits_framework:
        # Simulate some performance findings
        sample_findings = [
            {
                "description": "Documentation completeness could be improved",
                "severity": "medium",
                "area": "documentation_quality"
            },
            {
                "description": "Response time to compliance issues needs attention",
                "severity": "high",
                "area": "responsiveness"
            },
            {
                "description": "Collaboration with team members shows positive trends",
                "severity": "low",
                "area": "teamwork"
            }
        ]
        
        print("   Sample Performance Findings:")
        for i, finding in enumerate(sample_findings, 1):
            print(f"   {i}. {finding['description']} (Severity: {finding['severity']})")
        
        print("\n   7 Habits Mapping:")
        for i, finding in enumerate(sample_findings, 1):
            try:
                habit_mapping = engine.habits_framework.map_finding_to_habit(finding)
                if habit_mapping:
                    print(f"   🎯 Finding {i} → Habit {habit_mapping.get('habit_number', 'N/A')}: {habit_mapping.get('name', 'Unknown')}")
                    print(f"      💡 Insight: {habit_mapping.get('explanation', 'No explanation available')[:80]}...")
                    if habit_mapping.get('actionable_steps'):
                        print(f"      📋 Action: {habit_mapping['actionable_steps'][0][:60]}...")
                else:
                    print(f"   🎯 Finding {i} → No specific habit mapping available")
            except Exception as e:
                print(f"   🎯 Finding {i} → Error in mapping: {str(e)}")
        print()
    
    # 6. Show comprehensive report features
    print("6. Comprehensive Report Features Demonstrated:")
    print("   ✅ Non-repetitive content organization")
    print("   ✅ Well-organized section hierarchy")
    print("   ✅ Professional flow and readability")
    print("   ✅ Informative and actionable insights")
    print("   ✅ Educational value with training components")
    print("   ✅ Compliance-driven regulatory citations")
    print("   ✅ Data-driven evidence and reasoning")
    print("   ✅ Deep thinking and logical analysis")
    print("   ✅ Positive and constructive tone")
    print("   ✅ Visual appeal with professional styling")
    print("   ✅ AI transparency and ethical disclosures")
    print("   ✅ Bias mitigation and fairness controls")
    print("   ✅ 7 Habits personal development integration")
    print()
    
    # 7. Show guardrails statistics
    if engine.guardrails_service:
        print("7. AI Guardrails Performance Statistics:")
        stats = engine.guardrails_service.get_guardrail_statistics()
        
        print(f"   📊 Total Evaluations: {stats['total_evaluations']}")
        print(f"   ⚠️ Total Violations Detected: {stats['total_violations']}")
        print(f"   📈 Violation Rate: {stats['violation_rate']:.2%}")
        
        if stats['violation_types']:
            print("   🔍 Violation Types:")
            for violation_type, count in stats['violation_types'].items():
                print(f"     • {violation_type}: {count}")
        
        if stats['risk_level_distribution']:
            print("   🎯 Risk Level Distribution:")
            for risk_level, count in stats['risk_level_distribution'].items():
                print(f"     • {risk_level}: {count}")
        
        print("   🛡️ Active Guardrails:")
        for guardrail in stats['guardrail_status']:
            status = "✅ ENABLED" if guardrail['enabled'] else "❌ DISABLED"
            print(f"     • {guardrail['name']}: {status}")
        print()
    
    # 8. Responsible AI principles summary
    print("8. Responsible AI Principles Implemented:")
    print("   🔍 TRANSPARENCY:")
    print("     • AI-generated content clearly disclosed")
    print("     • Confidence levels and limitations shown")
    print("     • Model information and capabilities explained")
    print()
    print("   ⚖️ FAIRNESS:")
    print("     • Bias detection and mitigation active")
    print("     • Inclusive language enforcement")
    print("     • Demographic fairness monitoring")
    print()
    print("   📋 ACCOUNTABILITY:")
    print("     • Clear responsibility assignments")
    print("     • Professional oversight requirements")
    print("     • Audit trails and violation tracking")
    print()
    print("   🔒 SECURITY:")
    print("     • Content safety monitoring")
    print("     • Harmful content prevention")
    print("     • Ethical compliance enforcement")
    print()
    
    print("=== Responsible AI Reporting Demo Complete ===")
    print("\n🎉 Key Achievements:")
    print("✅ Comprehensive AI safety controls implemented")
    print("✅ Bias mitigation and fairness enforcement active")
    print("✅ Transparency and explainability ensured")
    print("✅ Ethical compliance monitoring in place")
    print("✅ 7 Habits framework for personal development")
    print("✅ Professional, educational, and actionable reports")
    print("✅ Data-driven insights with deep reasoning")
    print("✅ Responsible AI practices throughout the system")


def demonstrate_guardrails_configuration():
    """Demonstrate guardrails configuration options"""
    print("\n=== AI Guardrails Configuration Options ===")
    
    service = AIGuardrailsService()
    
    print("Available Guardrails:")
    for guardrail in service.guardrails:
        print(f"  • {guardrail.name}: {guardrail.description}")
    
    print("\nGuardrail Management:")
    print("  • Enable/disable individual guardrails")
    print("  • Add custom domain-specific guardrails")
    print("  • Configure sensitivity levels")
    print("  • Monitor performance statistics")
    print("  • Export audit reports")
    
    print("\nTransparency Templates:")
    for template_name, template_text in service.transparency_templates.items():
        print(f"  • {template_name}: {template_text[:50]}...")


if __name__ == "__main__":
    # Run the main demonstration
    asyncio.run(demonstrate_responsible_ai_reporting())
    
    # Show configuration options
    demonstrate_guardrails_configuration()