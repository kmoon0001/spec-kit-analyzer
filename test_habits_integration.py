#!/usr/bin/env python3
"""Test 7 Habits Framework Integration"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.enhanced_habit_mapper import SevenHabitsFramework
from src.core.analysis_service import AnalysisService
from src.config import get_settings

def test_habits_framework():
    """Test if 7 Habits Framework is working"""
    print("Testing 7 Habits Framework Integration...")

    # Test 1: Direct framework test
    print("\n1. Testing SevenHabitsFramework directly...")
    try:
        habits_framework = SevenHabitsFramework()
        print("[OK] SevenHabitsFramework initialized successfully")

        # Test mapping a finding
        test_finding = {
            "issue_title": "Incomplete documentation",
            "text": "Missing required elements in treatment plan",
            "risk": "HIGH"
        }

        habit_info = habits_framework.map_finding_to_habit(test_finding)
        print(f"[OK] Habit mapping test: {habit_info['name']} (Habit {habit_info['habit_number']})")
        print(f"   Confidence: {habit_info['confidence']:.2f}")
        print(f"   Explanation: {habit_info['explanation']}")

    except Exception as e:
        print(f"[ERROR] SevenHabitsFramework test failed: {e}")
        return False

    # Test 2: AnalysisService integration
    print("\n2. Testing AnalysisService integration...")
    try:
        settings = get_settings()
        print(f"[OK] Habits framework enabled in config: {settings.habits_framework.enabled}")

        # Create AnalysisService (this will initialize habits framework)
        analysis_service = AnalysisService()

        if hasattr(analysis_service, 'habits_framework') and analysis_service.habits_framework:
            print("[OK] AnalysisService has habits_framework initialized")
        else:
            print("[ERROR] AnalysisService does not have habits_framework")
            return False

        # Test report generator integration
        if hasattr(analysis_service, 'report_generator') and analysis_service.report_generator:
            if hasattr(analysis_service.report_generator, 'habits_framework'):
                print("[OK] ReportGenerator has habits_framework")
            else:
                print("[ERROR] ReportGenerator does not have habits_framework")
                return False
        else:
            print("[ERROR] AnalysisService does not have report_generator")
            return False

    except Exception as e:
        print(f"[ERROR] AnalysisService integration test failed: {e}")
        return False

    # Test 3: Configuration test
    print("\n3. Testing configuration...")
    try:
        settings = get_settings()
        habits_config = settings.habits_framework

        print(f"[OK] Habits enabled: {habits_config.enabled}")
        print(f"[OK] Visibility level: {habits_config.visibility_level}")
        print(f"[OK] AI features enabled: {habits_config.ai_features.use_ai_mapping}")

    except Exception as e:
        print(f"[ERROR] Configuration test failed: {e}")
        return False

    print("\n[SUCCESS] All 7 Habits Framework tests passed!")
    return True

def test_habits_in_report():
    """Test if habits appear in generated reports"""
    print("\n4. Testing habits in report generation...")

    try:
        from src.core.report_generator import ReportGenerator

        # Create report generator
        report_gen = ReportGenerator()

        if report_gen.habits_framework:
            print("[OK] ReportGenerator has habits framework")

            # Test habit mapping
            test_finding = {
                "issue_title": "Vague documentation",
                "text": "Unclear treatment goals and objectives",
                "risk": "MEDIUM"
            }

            habit_info = report_gen._get_habit_info_for_finding(test_finding)
            if habit_info:
                print(f"[OK] Habit mapping in report: {habit_info['name']}")
                print(f"   Habit number: {habit_info['habit_number']}")
                print(f"   Confidence: {habit_info.get('confidence', 'N/A')}")
            else:
                print("[ERROR] No habit info returned for test finding")
                return False
        else:
            print("[ERROR] ReportGenerator does not have habits framework")
            return False

    except Exception as e:
        print(f"[ERROR] Report generation test failed: {e}")
        return False

    print("[OK] Habits integration in reports working!")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("7 HABITS FRAMEWORK INTEGRATION TEST")
    print("=" * 60)

    success = test_habits_framework()
    if success:
        success = test_habits_in_report()

    if success:
        print("\n[SUCCESS] ALL TESTS PASSED! 7 Habits Framework is properly integrated!")
        print("\nThe 7 Habits should now appear in your analysis reports.")
        print("Look for habit tags in the compliance findings and habit insights sections.")
    else:
        print("\n[ERROR] Some tests failed. Check the errors above.")

    print("=" * 60)
