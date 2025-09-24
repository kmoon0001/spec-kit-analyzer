import os
from src.compliance_analyzer import ComplianceAnalyzer
from src.utils import load_config
from src.guideline_service import GuidelineService
from src.core.hybrid_retriever import HybridRetriever

def test_analyze_document():
    config = load_config()
    guideline_service = GuidelineService(sources=config.get('guideline_sources', []))
    retriever = HybridRetriever(config['models']['retriever'])
    analyzer = ComplianceAnalyzer(config, guideline_service, retriever)

    # Create a dummy document
    with open("test_document.txt", "w") as f:
        f.write("This is a test document.")

    analysis_result = analyzer.analyze_document("This is a test document.", "PT", "evaluation")
    assert "findings" in analysis_result
    assert isinstance(analysis_result["findings"], list)

    # Clean up the dummy document
    os.remove("test_document.txt")