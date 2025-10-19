#!/usr/bin/env python3
"""Test 7 Habits in Real Analysis"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.analysis_service import AnalysisService
from src.core.report_generator import ReportGenerator

def test_habits_in_real_analysis():
    """Test 7 Habits with a document that will generate findings"""
    print("Testing 7 Habits Framework in Real Analysis...")

    # Create analysis service
    analysis_service = AnalysisService()

    # Test document with compliance issues that should trigger habits
    test_document = """
    PHYSICAL THERAPY EVALUATION

    Patient: John Doe
    Date: 2024-01-15

    CHIEF COMPLAINT: Patient reports lower back pain

    HISTORY OF PRESENT ILLNESS: Patient has been experiencing lower back pain for 2 weeks.
    Pain is worse in the morning and improves with activity.

    ASSESSMENT: Lower back pain, likely musculoskeletal in nature.

    PLAN:
    - Patient education
    - Home exercise program
    - Follow up in 2 weeks

    Note: Treatment goals not clearly defined. Medical necessity not well documented.
    Functional limitations not assessed. Progress measures not established.
    """

    print("\nAnalyzing test document with compliance issues...")

    async def run_analysis():
        try:
            # Run analysis
            result = await analysis_service.analyze_document(
                discipline="pt",
                document_text=test_document,
                progress_callback=lambda p, m: print(f"Progress: {p}% - {m}")
            )

            print(f"\nAnalysis completed. Result type: {type(result)}")

            # Check if result has analysis data
            if hasattr(result, 'analysis') and result.analysis:
                analysis_data = result.analysis
                print(f"Analysis data keys: {list(analysis_data.keys())}")

                # Look for findings
                findings = analysis_data.get('findings', [])
                print(f"Number of findings: {len(findings)}")

                if findings:
                    print("\nFindings with 7 Habits mapping:")
                    for i, finding in enumerate(findings):
                        print(f"\nFinding {i+1}:")
                        print(f"  Issue: {finding.get('issue_title', 'N/A')}")
                        print(f"  Text: {finding.get('text', 'N/A')[:100]}...")
                        print(f"  Risk: {finding.get('risk', 'N/A')}")

                        # Test habit mapping
                        if analysis_service.habits_framework:
                            habit_info = analysis_service.habits_framework.map_finding_to_habit(finding)
                            print(f"  Habit: {habit_info['name']} (Habit {habit_info['habit_number']})")
                            print(f"  Confidence: {habit_info['confidence']:.2f}")
                            print(f"  Explanation: {habit_info['explanation']}")
                else:
                    print("No findings generated (likely using mocks)")

            # Test report generation
            print("\nTesting report generation with habits...")
            report_gen = ReportGenerator(llm_service=analysis_service.llm_service)

            if report_gen.habits_framework:
                print("[OK] ReportGenerator has habits framework")

                # Generate a test report
                test_analysis = {
                    "findings": [
                        {
                            "issue_title": "Incomplete documentation",
                            "text": "Missing required elements in treatment plan",
                            "risk": "HIGH"
                        }
                    ],
                    "metadata": {"discipline": "pt"}
                }

                report = report_gen.generate_report(test_analysis)
                print(f"Report generated. Keys: {list(report.keys())}")

                # Check if report HTML contains habit information
                report_html = report.get('report_html', '')
                if 'habit' in report_html.lower():
                    print("[OK] Report HTML contains habit information!")
                else:
                    print("[INFO] Report HTML does not contain habit information (may be in different section)")

            else:
                print("[ERROR] ReportGenerator does not have habits framework")

        except Exception as e:
            print(f"[ERROR] Analysis failed: {e}")
            import traceback
            traceback.print_exc()

    # Run the async function
    asyncio.run(run_analysis())

if __name__ == "__main__":
    print("=" * 60)
    print("7 HABITS IN REAL ANALYSIS TEST")
    print("=" * 60)

    test_habits_in_real_analysis()

    print("=" * 60)
