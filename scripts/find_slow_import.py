#!/usr/bin/env python3
"""Find which specific import is causing the 2+ minute delay."""

import time


def test_import(module_name, description):
    """Test a single import and time it."""
    print(f"Testing {description}...", end=" ", flush=True)
    start = time.time()
    try:
        exec(f"import {module_name}")
        duration = time.time() - start
        if duration > 1.0:
            print(f"⚠️  SLOW: {duration:.2f}s")
        else:
            print(f"✅ {duration:.2f}s")
        return duration
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return 0


def test_from_import(import_stmt, description):
    """Test a from import and time it."""
    print(f"Testing {description}...", end=" ", flush=True)
    start = time.time()
    try:
        exec(import_stmt)
        duration = time.time() - start
        if duration > 1.0:
            print(f"⚠️  SLOW: {duration:.2f}s")
        else:
            print(f"✅ {duration:.2f}s")
        return duration
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return 0


print("=== Finding Slow Imports ===\n")

# Test core modules that might be heavy
slow_suspects = [
    ("src.core.llm_service", "LLM Service"),
    ("src.core.ner", "Named Entity Recognition"),
    ("src.core.hybrid_retriever", "Hybrid Retriever"),
    ("src.core.compliance_analyzer", "Compliance Analyzer"),
    ("src.core.document_analysis_service", "Document Analysis Service"),
    ("src.core.preprocessing_service", "Preprocessing Service"),
    ("src.core.fact_checker_service", "Fact Checker Service"),
    ("src.core.nlg_service", "NLG Service"),
    ("src.core.performance_manager", "Performance Manager"),
    ("transformers", "Transformers Library"),
    ("sentence_transformers", "Sentence Transformers"),
    ("ctransformers", "CTransformers"),
    ("faiss", "FAISS"),
    ("nltk", "NLTK"),
    ("spacy", "SpaCy"),
]

total_time = 0
for module, desc in slow_suspects:
    duration = test_import(module, desc)
    total_time += duration
    if duration > 5:
        print(f"🚨 FOUND CULPRIT: {module} took {duration:.2f}s")

print(f"\nTotal time for all imports: {total_time:.2f}s")

# Test specific from imports that might be problematic
print("\n=== Testing Specific From Imports ===")

from_imports = [
    ("from src.gui.dialogs.rubric_manager_dialog import RubricManagerDialog", "Rubric Manager"),
    ("from src.gui.workers.analysis_starter_worker import AnalysisStarterWorker", "Analysis Worker"),
    ("from src.core.analysis_service import AnalysisService", "Analysis Service"),
]

for import_stmt, desc in from_imports:
    test_from_import(import_stmt, desc)
