"""
Live test of the Therapy Compliance Analyzer with real AI analysis.
This script tests the full pipeline including the LLM.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.analysis_service import AnalysisService
from src.core.hybrid_retriever import HybridRetriever


async def test_real_analysis():
    """Run a real analysis with the LLM."""
    
    print("=" * 80)
    print("🚀 LIVE TEST: Therapy Compliance Analyzer with AI")
    print("=" * 80)
    
    # Initialize services
    print("\n📦 Initializing services...")
    retriever = HybridRetriever()
    analysis_service = AnalysisService(retriever=retriever)
    
    # Check if LLM is ready
    print(f"\n🤖 LLM Status: {'✅ READY' if analysis_service.llm_service.is_ready() else '❌ NOT READY'}")
    print(f"🧠 NER Status: {'✅ READY' if analysis_service.ner_analyzer else '❌ NOT READY'}")
    print(f"🔍 Retriever Status: {'✅ READY' if analysis_service.retriever else '❌ NOT READY'}")
    
    # Test document path
    test_file = "test_data/test_therapy_note.txt"
    
    if not Path(test_file).exists():
        print(f"\n❌ Test file not found: {test_file}")
        return
    
    print(f"\n📄 Analyzing document: {test_file}")
    print("⏳ This will take 30-60 seconds with AI processing...")
    print()
    
    # Run analysis
    try:
        result = await analysis_service.analyze_document(
            document_text=Path(test_file).read_text(encoding='utf-8'),
            discipline="PT",
        )
        
        print("\n" + "=" * 80)
        print("✅ ANALYSIS COMPLETE")
        print("=" * 80)
        
        # Display results
        print(f"\n📊 Overall Compliance Score: {result.get('compliance_score', 'N/A')}")
        print(f"🎯 Risk Level: {result.get('risk_level', 'N/A')}")
        print(f"🔍 Total Findings: {len(result.get('findings', []))}")
        
        # Show findings
        findings = result.get('findings', [])
        if findings:
            print("\n📋 COMPLIANCE FINDINGS:")
            print("-" * 80)
            for i, finding in enumerate(findings[:5], 1):  # Show first 5
                print(f"\n{i}. {finding.get('issue', 'Unknown issue')}")
                print(f"   Risk: {finding.get('severity', 'N/A')}")
                print(f"   Confidence: {finding.get('confidence', 'N/A')}")
                if finding.get('recommendation'):
                    print(f"   💡 Recommendation: {finding['recommendation'][:100]}...")
            
            if len(findings) > 5:
                print(f"\n... and {len(findings) - 5} more findings")
        
        # Show AI reasoning if available
        if result.get('reasoning'):
            print("\n🧠 AI REASONING:")
            print("-" * 80)
            print(result['reasoning'][:300] + "..." if len(result['reasoning']) > 300 else result['reasoning'])
        
        # Show NER entities
        entities = result.get('entities', [])
        if entities:
            print(f"\n🏷️  EXTRACTED ENTITIES: {len(entities)} found")
            entity_types = {}
            for entity in entities:
                entity_type = entity.get('type', 'Unknown')
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            for entity_type, count in sorted(entity_types.items()):
                print(f"   - {entity_type}: {count}")
        
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ ANALYSIS FAILED")
        print("=" * 80)
        print(f"\nError: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return False
    
    return True


async def test_llm_only():
    """Quick test of just the LLM service."""
    print("\n" + "=" * 80)
    print("🧪 QUICK LLM TEST")
    print("=" * 80)
    
    from src.core.llm_service import LLMService
    
    llm = LLMService()
    
    if not llm.is_ready():
        print("\n❌ LLM not ready. Please ensure models are downloaded.")
        return False
    
    print("\n✅ LLM is ready!")
    print("\n📝 Testing simple prompt...")
    
    test_prompt = "What are the key elements of a compliant physical therapy progress note?"
    
    try:
        response = llm.generate(test_prompt, max_tokens=150)
        print(f"\n🤖 LLM Response:\n{response}")
        print("\n✅ LLM test passed!")
        return True
    except Exception as e:
        print(f"\n❌ LLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Live test of Therapy Compliance Analyzer")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick LLM-only test instead of full analysis"
    )
    
    args = parser.parse_args()
    
    if args.quick:
        success = asyncio.run(test_llm_only())
    else:
        success = asyncio.run(test_real_analysis())
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
