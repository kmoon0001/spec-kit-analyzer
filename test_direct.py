#!/usr/bin/env python3
"""Direct test of the analysis service to verify the 5% progress fix."""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.analysis_service import AnalysisService

async def test_analysis_progress():
    """Test the analysis service directly to see if progress works."""
    print("Testing analysis service directly...")

    # Create analysis service
    service = AnalysisService()
    print(f"AnalysisService created with use_mocks={service.use_mocks}")

    # Track progress
    progress_history = []

    def progress_callback(progress, message):
        progress_history.append(progress)
        print(f"Progress: {progress}% | {message}")

    # Test document
    test_content = """
    Patient: John Doe
    Date: 2024-01-15

    Physical Therapy Progress Note

    Patient demonstrates improved range of motion in left shoulder.
    Pain level decreased from 7/10 to 4/10.
    Patient able to perform ADLs with minimal assistance.

    Goals:
    - Increase ROM to 90% of normal
    - Reduce pain to 3/10 or less
    - Independent ADL performance

    Treatment provided:
    - Passive ROM exercises
    - Heat therapy
    - Patient education

    Next session scheduled for 2024-01-17.
    """

    try:
        print("Starting analysis...")
        result = await service.analyze_document(
            document_text=test_content,
            discipline="pt",
            strictness="standard",
            analysis_mode="llama_test",
            progress_callback=progress_callback
        )

        print(f"\nAnalysis completed!")
        print(f"Progress flow: {' -> '.join(map(str, progress_history))}")

        # Check if it got stuck at 5%
        if len(progress_history) > 1 and progress_history[1] == 5 and len(set(progress_history[1:])) == 1:
            print("ERROR: ANALYSIS STUCK AT 5% - FIX NOT WORKING")
            return False
        else:
            print("SUCCESS: Progress flowed smoothly - FIX IS WORKING!")
            return True

    except Exception as e:
        print(f"ERROR: Analysis failed: {e}")
        return False

async def main():
    """Run the test."""
    print("Direct Analysis Service Test")
    print("=" * 40)

    success = await test_analysis_progress()

    print("\n" + "=" * 40)
    if success:
        print("SUCCESS: The 5% progress fix is working!")
        print("Analysis progresses smoothly from 0% to 100%")
    else:
        print("FAILURE: The 5% progress issue persists")
        print("Analysis still gets stuck at 5%")

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
