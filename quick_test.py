#!/usr/bin/env python3
"""
Quick test to verify everything is working.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("🧪 QUICK TEST - Therapy Compliance Analyzer")
    print("=" * 50)
    
    try:
        # Test NER
        from src.core.ner import NERAnalyzer
        print("✅ NER module imported")
        
        analyzer = NERAnalyzer(model_names=[])
        print("✅ NER analyzer crea