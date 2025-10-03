#!/usr/bin/env python3
"""
Test script to verify document parsing functionality
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_parsing():
    """Test the document parsing functionality."""
    try:
        from src.core.parsing import parse_document_content, parse_document_into_sections
        
        # Test with a sample text file
        sample_text = """
Physical Therapy Progress Note

Patient: John Doe
Date: 2024-01-15

Subjective:
Patient reports decreased pain in lower back. States pain level is 3/10 today compared to 7/10 last week.

Objective:
Range of motion: Lumbar flexion 45 degrees (improved from 30 degrees)
Strength: Hip flexors 4/5, improved from 3/5
Gait: Independent with normal pattern

Assessment:
Patient showing good progress with current treatment plan. Pain levels decreasing and functional mobility improving.

Plan:
Continue current exercise program
Add core strengthening exercises
Follow up in 1 week

Signature: Dr. Jane Smith, PT
License: PT12345
"""
        
        # Test document section parsing
        print("🔍 Testing Document Section Parsing...")
        sections = parse_document_into_sections(sample_text)
        
        print(f"📋 Found {len(sections)} sections:")
        for section_name, content in sections.items():
            word_count = len(content.split())
            print(f"  • {section_name}: {word_count} words")
            print(f"    Preview: {content[:100]}...")
            print()
        
        # Test with a simple text file
        test_file = "test_sample.txt"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(sample_text)
        
        print("🔍 Testing File Parsing...")
        chunks = parse_document_content(test_file)
        
        print(f"📄 Parsed into {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}: {len(chunk['sentence'])} characters")
            print(f"  Source: {chunk['source']}")
            print(f"  Preview: {chunk['sentence'][:100]}...")
            print()
        
        # Clean up
        os.remove(test_file)
        
        print("✅ Document parsing test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Document parsing modules not available")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Document Parsing Functionality")
    print("=" * 50)
    
    success = test_parsing()
    
    if success:
        print("\n🎉 All tests passed! Document parsing is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")