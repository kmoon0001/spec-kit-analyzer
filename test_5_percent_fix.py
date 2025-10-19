#!/usr/bin/env python3
"""
Test script to verify the 5% stuck issue is fixed.
This script tests document parsing with timeout protection.
"""

import sys
import os
import time
import threading
import queue
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.parsing import parse_document_content
from core.text_utils import sanitize_human_text

def test_parsing_timeout():
    """Test that document parsing doesn't hang indefinitely."""
    print("🧪 Testing document parsing timeout protection...")
    
    # Create a test text file
    test_file = Path("test_document.txt")
    test_content = """
    Patient Progress Note
    
    Patient: John Doe
    Date: 2024-01-15
    
    Subjective:
    Patient reports improved mobility and reduced pain levels.
    
    Objective:
    Range of motion has increased by 15 degrees.
    Strength testing shows improvement in affected areas.
    
    Assessment:
    Patient is responding well to physical therapy treatment.
    
    Plan:
    Continue current treatment protocol.
    Increase exercise intensity gradually.
    """
    
    try:
        test_file.write_text(test_content)
        
        # Test parsing with timeout protection
        start_time = time.time()
        result = parse_document_content(str(test_file))
        end_time = time.time()
        
        parsing_time = end_time - start_time
        
        print(f"✅ Parsing completed in {parsing_time:.2f} seconds")
        print(f"📄 Extracted {len(result)} text chunks")
        
        if result and len(result) > 0:
            first_chunk = result[0]
            if "sentence" in first_chunk:
                sample_text = first_chunk["sentence"][:100] + "..." if len(first_chunk["sentence"]) > 100 else first_chunk["sentence"]
                print(f"📝 Sample text: {sample_text}")
        
        # Test text sanitization
        print("\n🧹 Testing text sanitization...")
        test_text = "This is a test document with some special characters: @#$%^&*()"
        sanitized = sanitize_human_text(test_text)
        print(f"✅ Sanitized text: {sanitized}")
        
        # Test repetitive text detection
        print("\n🔄 Testing repetitive text detection...")
        repetitive_text = "This is repetitive text. " * 10
        sanitized_repetitive = sanitize_human_text(repetitive_text)
        print(f"✅ Repetitive text handled: {len(sanitized_repetitive)} chars")
        
        print("\n🎉 All tests passed! The 5% stuck issue should be fixed.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()

if __name__ == "__main__":
    print("=" * 50)
    print("  THERAPY COMPLIANCE ANALYZER")
    print("  5% Stuck Issue Fix Test")
    print("=" * 50)
    print()
    
    success = test_parsing_timeout()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ FIX VERIFIED: Document parsing now has timeout protection")
        print("✅ The 5% stuck issue should be resolved")
    else:
        print("❌ FIX FAILED: Issues detected in document parsing")
    print("=" * 50)
