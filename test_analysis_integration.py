#!/usr/bin/env python3
"""
Test script to verify AnalysisService integration with GUI
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_analysis_service_integration():
    """Test that AnalysisService can handle document text input from GUI"""
    try:
        from src.core.analysis_service import AnalysisService
        
        # Create service instance
        service = AnalysisService()
        
        # Test document text (sample therapy note)
        test_document = """
        Patient: John Doe
        Date: 2024-01-15
        
        PROGRESS NOTE - Physical Therapy
        
        Patient continues to show improvement in range of motion following knee surgery.
        Performed therapeutic exercises including:
        - Quadriceps strengthening
        - Range of motion exercises
        - Gait training
        
        Patient tolerated treatment well. Plan to continue current treatment protocol.
        
        Therapist: Jane Smith, PT
        """
        
        print("Testing AnalysisService with document text...")
        
        # Test the analysis
        result = service.analyze_document(
            document_text=test_document,
            discipline="pt"
        )
        
        print("✅ Analysis completed successfully!")
        print(f"Result type: {type(result)}")
        
        # If it's a coroutine, we need to handle it
        if hasattr(result, '__await__'):
            import asyncio
            result = asyncio.run(result)
        
        print(f"Analysis result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return False

if __name__ == "__main__":
    success = test_analysis_service_integration()
    sys.exit(0 if success else 1)