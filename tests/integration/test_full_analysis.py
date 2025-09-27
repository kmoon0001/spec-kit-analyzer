`python
  import os
  import pytest
  from unittest.mock import patch

from src.core.analysis_service import AnalysisService

  # A fixture to create a dummy config.yaml for testing
  @pytest.fixture(scope="module")
  def mock_config_file(tmpdir_factory):
      config_content = '''
  models:
    ner_ensemble: ["dslim/bert-base-NER"]
    retriever: "sentence-transformers/all-MiniLM-L6-v2"
    generator: "sshleifer/distilbart-cnn-6-6"
    fact_checker: "google/flan-t5-small"
    doc_classifier_prompt: "src/core/prompts/doc_classifier_prompt.txt"
    analysis_prompt_template: "src/core/prompts/analysis_prompt.txt"

  llm_settings:
    gpu_layers: 0

  retrieval_settings:
    similarity_top_k: 3
  '''
      config_file = tmpdir_factory.mktemp("data").join("config.yaml")
      # Create dummy prompt files
      os.makedirs(os.path.dirname(str(config_file)), exist_ok=True)
      os.makedirs("src/core/prompts", exist_ok=True)
      with open("src/core/prompts/doc_classifier_prompt.txt", "w") as f: f.write("Classify: {document}")
      with open("src/core/prompts/analysis_prompt.txt", "w") as f: f.write("Analyze: {document}")

      with open(str(config_file), "w") as f:
          f.write(config_content)
      return str(config_file)

  # A fixture to create a dummy document for analysis
  @pytest.fixture
  def dummy_document(tmpdir):
      doc_content = "The patient shows improvement but lacks quantifiable progress."
      doc_file = tmpdir.join("test_document.txt")
      with open(str(doc_file), "w") as f:
          f.write(doc_content)
      return str(doc_file)

  @pytest.mark.slow
  @patch('src.core.analysis_service.LLMService')
  @patch('src.core.analysis_service.HybridRetriever')
  def test_full_analysis_pipeline(MockHybridRetriever, MockLLMService, dummy_document, mock_config_file):
      """
      Tests the full analysis pipeline with a mocked LLM and Retriever to ensure
      the service orchestration works as expected.
      """
      # --- Arrange ---
      # Mock the LLM service to return a predictable JSON structure
      mock_llm = MockLLMService.return_value
      mock_llm.generate_text.return_value = '''`json
      {
          "findings": [
              {
                  "text": "lacks quantifiable progress",
                  "risk": "Moderate",
                  "suggestion": "Use standardized measurements.",
                  "rule_id": "GH-001"
              }
          ]
      }
      '''
      mock_llm.parse_json_output.return_value = {
          "findings": [
              {
                  "text": "lacks quantifiable progress",
                  "risk": "Moderate",
                  "suggestion": "Use standardized measurements.",
                  "rule_id": "GH-001"
              }
          ]
      }

  Mock the retriever to return a predictable rule
  --- Act ---
  --- Assert ---
  Check that data from the mocked LLM and Retriever is present
  `