#!/usr/bin/env python3
"""
Enhanced Accuracy System Test
Tests the system with all safe accuracy improvements
"""

import asyncio
from src.core.analysis_service import AnalysisService

async def test_enhanced_system():
    print('Testing Enhanced Accuracy System with Safe Improvements')
    print('=' * 60)

    # Create analysis service
    service = AnalysisService(use_mocks=True)

    # Test document
    document_text = '''
    Patient John Doe presented with acute lower back pain following a work injury.
    Initial assessment shows limited range of motion and muscle spasms.
    Treatment plan includes physical therapy exercises, pain management, and activity modification.
    Patient demonstrates good understanding of home exercise program.
    Progress noted in range of motion and pain reduction.
    Next appointment scheduled for follow-up assessment.
    '''

    print('Document:', document_text.strip()[:100] + '...')
    print()

    # Run analysis with progress tracking
    def progress_callback(percentage, message):
        print(f'Progress: {percentage}% | {message}')

    print('Running Enhanced Analysis...')
    result = await service.analyze_document(
        document_text=document_text,
        discipline='pt',
        progress_callback=progress_callback
    )

    print()
    print('Analysis Complete!')
    print('=' * 60)

    # Show key results
    if isinstance(result, dict):
        print('Key Results:')
        print(f'  - Compliance Score: {result.get("compliance_score", "N/A")}')
        print(f'  - Findings Count: {len(result.get("findings", []))}')
        print(f'  - Confidence: {result.get("confidence", "N/A")}')

        # Check for safe accuracy improvements
        safe_improvements = result.get('safe_accuracy_improvements', {})
        if safe_improvements:
            print('Safe Accuracy Improvements Applied:')
            print(f'  - Strategies: {len(safe_improvements.get("applied_strategies", []))}')
            print(f'  - Improvement Score: {safe_improvements.get("overall_improvement_score", 0):.2f}')
            print(f'  - Safety Score: {safe_improvements.get("safety_score", 0):.2f}')

        # Check for accuracy validation
        accuracy_validation = result.get('accuracy_validation', {})
        if accuracy_validation:
            print('Accuracy Validation:')
            print(f'  - Status: {accuracy_validation.get("validation_status", "N/A")}')
            print(f'  - Confidence Score: {accuracy_validation.get("confidence_score", 0):.2f}')
            print(f'  - Hallucination Rate: {accuracy_validation.get("hallucination_rate", 0):.2f}')

    print()
    print('Enhanced Accuracy System Test Complete!')

if __name__ == "__main__":
    asyncio.run(test_enhanced_system())
