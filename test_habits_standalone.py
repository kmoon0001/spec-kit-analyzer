"""
Standalone test for Enhanced 7 Habits Framework.
Quick validation without pytest dependencies.
"""

from src.core.enhanced_habit_mapper import SevenHabitsFramework, get_habit_for_finding


def test_all_features():
    """Run all habit framework tests."""
    print("\n=== Testing Enhanced 7 Habits Framework ===\n")

    # Test 1: All 7 habits present
    print("1. Testing all 7 habits are present...")
    framework = SevenHabitsFramework()
    assert len(framework.HABITS) == 7
    for i in range(1, 8):
        assert f"habit_{i}" in framework.HABITS
    print("   ✓ All 7 habits present")

    # Test 2: Rule-based mapping
    print("2. Testing rule-based habit mapping...")
    
    test_cases = [
        ({"issue_title": "Missing signature", "text": "Not signed"}, 3, "Put First Things First"),
        ({"issue_title": "Goals not measurable", "text": "Lacks specificity"}, 2, "Begin with the End"),
        ({"issue_title": "Poor collaboration", "text": "Team communication"}, 4, "Think Win-Win"),
        ({"issue_title": "Medical necessity unclear", "text": "Skilled service"}, 5, "Seek First to Understand"),
        ({"issue_title": "Inconsistent documentation", "text": "Alignment issues"}, 6, "Synergize"),
        ({"issue_title": "Outdated practices", "text": "Need training"}, 7, "Sharpen the Saw"),
    ]
    
    for finding, expected_number, expected_name_part in test_cases:
        result = framework.map_finding_to_habit(finding)
        assert result["habit_number"] == expected_number, f"Expected habit {expected_number}, got {result['habit_number']}"
        assert expected_name_part in result["name"], f"Expected '{expected_name_part}' in name"
    
    print("   ✓ Rule-based mapping works correctly")

    # Test 3: Habit details
    print("3. Testing habit details retrieval...")
    for habit_id in framework.HABITS:
        habit = framework.get_habit_details(habit_id)
        assert habit["number"] in range(1, 8)
        assert habit["name"]
        assert habit["principle"]
        assert habit["clinical_application"]
        assert len(habit["improvement_strategies"]) >= 4
        assert len(habit["clinical_examples"]) >= 4
    print("   ✓ All habits have complete details")

    # Test 4: Habit progression tracking
    print("4. Testing habit progression tracking...")
    findings_history = [
        {"habit_id": "habit_1"},
        {"habit_id": "habit_1"},
        {"habit_id": "habit_5"},
        {"habit_id": "habit_5"},
        {"habit_id": "habit_5"},
        {"habit_id": "habit_5"},
    ]
    
    metrics = framework.get_habit_progression_metrics(findings_history)
    assert metrics["total_findings"] == 6
    assert metrics["habit_breakdown"]["habit_1"]["finding_count"] == 2
    assert metrics["habit_breakdown"]["habit_5"]["finding_count"] == 4
    assert metrics["habit_breakdown"]["habit_5"]["needs_focus"] is True
    print("   ✓ Progression tracking works correctly")

    # Test 5: Mastery levels
    print("5. Testing mastery level calculation...")
    # Mastered: <5%
    findings_mastered = [{"habit_id": "habit_1"}] + [{"habit_id": "habit_2"}] * 99
    metrics_mastered = framework.get_habit_progression_metrics(findings_mastered)
    assert metrics_mastered["habit_breakdown"]["habit_1"]["mastery_level"] == "Mastered"
    
    # Needs Focus: >25%
    findings_needs_focus = [{"habit_id": "habit_1"}] * 30 + [{"habit_id": "habit_2"}] * 70
    metrics_needs_focus = framework.get_habit_progression_metrics(findings_needs_focus)
    assert metrics_needs_focus["habit_breakdown"]["habit_1"]["mastery_level"] == "Needs Focus"
    print("   ✓ Mastery levels calculated correctly")

    # Test 6: Backward compatibility
    print("6. Testing backward compatibility...")
    finding = {"issue_title": "Missing signature", "text": "Not signed"}
    result = get_habit_for_finding(finding)
    assert "name" in result
    assert "explanation" in result
    assert "Habit" in result["name"]
    print("   ✓ Backward compatibility maintained")

    # Test 7: Get all habits
    print("7. Testing get all habits...")
    all_habits = framework.get_all_habits()
    assert len(all_habits) == 7
    for habit in all_habits:
        assert "habit_id" in habit
        assert "number" in habit
        assert "name" in habit
    print("   ✓ Get all habits works correctly")

    # Test 8: New habits (4, 6, 7)
    print("8. Testing new habits (4, 6, 7)...")
    habit_4 = framework.get_habit_details("habit_4")
    assert habit_4["name"] == "Think Win-Win"
    assert "Interpersonal Leadership" in habit_4["principle"]
    
    habit_6 = framework.get_habit_details("habit_6")
    assert habit_6["name"] == "Synergize"
    assert "Creative Cooperation" in habit_6["principle"]
    
    habit_7 = framework.get_habit_details("habit_7")
    assert habit_7["name"] == "Sharpen the Saw"
    assert "Continuous Improvement" in habit_7["principle"]
    print("   ✓ New habits (4, 6, 7) implemented correctly")

    # Test 9: Confidence scoring
    print("9. Testing confidence scoring...")
    strong_match = {"issue_title": "Missing signature and date", "text": "Not signed timely"}
    weak_match = {"issue_title": "Random issue", "text": "No keywords"}
    
    result_strong = framework.map_finding_to_habit(strong_match)
    result_weak = framework.map_finding_to_habit(weak_match)
    
    assert result_strong["confidence"] > result_weak["confidence"]
    print("   ✓ Confidence scoring works correctly")

    # Test 10: Edge cases
    print("10. Testing edge cases...")
    empty_finding = {}
    result_empty = framework.map_finding_to_habit(empty_finding)
    assert result_empty["habit_number"] in range(1, 8)
    
    none_finding = {"issue_title": None, "text": None}
    result_none = framework.map_finding_to_habit(none_finding)
    assert result_none["habit_number"] in range(1, 8)
    print("   ✓ Edge cases handled correctly")

    print("\n=== All Enhanced 7 Habits Framework tests passed! ===\n")
    
    # Print summary
    print("Summary:")
    print("  ✓ All 7 habits implemented")
    print("  ✓ Rule-based mapping working")
    print("  ✓ Habit details complete")
    print("  ✓ Progression tracking functional")
    print("  ✓ Mastery levels calculated")
    print("  ✓ Backward compatible")
    print("  ✓ New habits (4, 6, 7) added")
    print("  ✓ Confidence scoring working")
    print("  ✓ Edge cases handled")
    print("\n✨ Framework is production-ready! ✨\n")


if __name__ == "__main__":
    test_all_features()
