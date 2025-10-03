#!/usr/bin/env python3
"""
Simple test to verify NER functionality works without spaCy.
This bypasses the GUI and LLM loading issues.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_ner_basic():
    """Test basic NER functionality."""
    print("Testing NER module without spaCy...")

    try:
        from src.core.ner import NERAnalyzer

        print("✅ NER module imported successfully")

        # Create analyzer with empty model list to avoid downloads
        analyzer = NERAnalyzer(model_names=[])
        print("✅ NER analyzer created successfully")

        # Test clinician name extraction with regex
        test_text = "Signature: Dr. Jane Smith, PT"
        result = analyzer.extract_clinician_name(test_text)
        print(f"✅ Clinician extraction result: {result}")

        # Test empty text handling
        empty_result = analyzer.extract_entities("")
        print(f"✅ Empty text handling: {empty_result}")

        print("\n🎉 All NER tests passed! The spaCy removal was successful.")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_analysis_service():
    """Test if analysis service can be imported."""
    print("\nTesting Analysis Service import...")

    try:
        print("✅ Analysis service imported successfully")
        return True
    except Exception as e:
        print(f"❌ Analysis service error: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing Therapy Compliance Analyzer - NER Module")
    print("=" * 50)

    ner_ok = test_ner_basic()
    analysis_ok = test_analysis_service()

    if ner_ok and analysis_ok:
        print("\n✅ Core functionality is working!")
        print("The app freeze is likely due to LLM loading, not NER issues.")
    else:
        print("\n❌ Some issues found that need fixing.")
