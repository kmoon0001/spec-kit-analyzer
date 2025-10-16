#!/usr/bin/env python3
"""
Debug script to test the analysis pipeline and identify hanging issues.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.analysis_service import AnalysisService

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_analysis():
    """Test the analysis pipeline with a simple document."""

    # Simple test document
    test_document = """
    Patient: John Doe
    Date: 2024-01-15

    Progress Note:
    Patient attended physical therapy session today.
    Worked on range of motion exercises for shoulder.
    Patient tolerated treatment well.
    Plan: Continue current treatment plan.

    Therapist: Jane Smith, PT
    """

    logger.info("Starting analysis test...")
    start_time = time.time()

    try:
        # Initialize analysis service
        logger.info("Initializing analysis service...")
        analysis_service = AnalysisService()

        # Run analysis
        logger.info("Running document analysis...")
        result = await analysis_service.analyze_document(
            document_text=test_document, discipline="pt", analysis_mode="rubric"
        )

        end_time = time.time()
        duration = end_time - start_time

        logger.info(f"Analysis completed successfully in {duration:.2f} seconds")
        logger.info(f"Result keys: {list(result.keys())}")

        if "analysis" in result:
            analysis = result["analysis"]
            logger.info(f"Analysis summary: {analysis.get('summary', 'No summary')}")
            logger.info(f"Number of findings: {len(analysis.get('findings', []))}")

        return True

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        logger.error(f"Analysis failed after {duration:.2f} seconds: {e}")
        logger.exception("Full error details:")
        return False


async def test_with_timeout():
    """Test analysis with a timeout to detect hanging."""
    try:
        # Set a 2-minute timeout for the entire test
        result = await asyncio.wait_for(test_analysis(), timeout=120.0)
        if result:
            print("✅ Analysis test PASSED")
        else:
            print("❌ Analysis test FAILED")
        return result
    except TimeoutError:
        print("⏰ Analysis test TIMED OUT after 2 minutes")
        print("This indicates the analysis pipeline is hanging somewhere")
        return False
    except Exception as e:
        print(f"💥 Analysis test CRASHED: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Testing Analysis Pipeline...")
    print("This will help identify where the analysis is hanging.")
    print("-" * 50)

    # Run the test
    success = asyncio.run(test_with_timeout())

    if success:
        print("\n🎉 Analysis pipeline is working correctly!")
    else:
        print("\n🚨 Analysis pipeline has issues that need to be fixed.")
        print("\nCommon causes:")
        print("- AI models not loading properly")
        print("- Network timeouts in model downloads")
        print("- Blocking operations without proper async handling")
        print("- Memory issues with large models")
