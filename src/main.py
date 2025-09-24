import argparse
import logging
from src.utils import load_config
from src.guideline_service import GuidelineService
from src.core.hybrid_retriever import HybridRetriever
from src.compliance_analyzer import ComplianceAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the compliance analysis CLI.
    """
    parser = argparse.ArgumentParser(description="Analyze clinical documents for compliance.")
    parser.add_argument("document_path", type=str, help="Path to the clinical document to analyze.")
    parser.add_argument("--discipline", type=str, required=True, help="Clinical discipline (e.g., PT, OT, SLP).")
    parser.add_argument("--doc_type", type=str, required=True, help="Document type (e.g., evaluation, progress_note).")
    args = parser.parse_args()

    # Load configuration
    config = load_config()

    # Initialize services
    guideline_service = GuidelineService(sources=config.get('guideline_sources', []))
    retriever = HybridRetriever(guideline_service)

    # Initialize the new ComplianceAnalyzer
    analyzer = ComplianceAnalyzer(config, guideline_service, retriever)

    # Read the document
    with open(args.document_path, 'r') as f:
        document_text = f.read()

    # Analyze the document
    analysis_result = analyzer.analyze_document(
        document=document_text,
        discipline=args.discipline,
        doc_type=args.doc_type
    )

    # Print the result
    logger.info("Compliance Analysis Result:")
    import json
    print(json.dumps(analysis_result, indent=2))

if __name__ == "__main__":
    main()