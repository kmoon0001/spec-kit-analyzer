import yaml
import logging
from src.core.llm_service import LLMService

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_medical_dictionary():
    """
    Uses the configured LLM to generate a large list of medical terms and save it to a file.
    This is a one-time script.
    """
    try:
        # 1. Load configuration to get LLM settings
        config_path = "config.yaml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # 2. Initialize the LLM Service
        llm_service = LLMService(
            model_repo_id=config["models"]["generator"],
            model_filename=config["models"].get("generator_filename"),
            llm_settings=config.get("llm_settings", {}),
        )

        if not llm_service.is_ready():
            logger.error("LLM Service is not ready. Cannot generate dictionary.")
            return

        # 3. Create a detailed prompt
        prompt = """
            You are an expert in medical terminology. Your task is to generate a comprehensive list of common medical terms, abbreviations, and their likely misspellings.

            Instructions:
            - The list should be as extensive as possible, covering multiple medical specialties (e.g., physical therapy, occupational therapy, cardiology, neurology).
            - Include common acronyms and their full names (e.g., "CHF (Congestive Heart Failure)").
            - For each term, provide a few common, plausible misspellings.
            - Format the output as a simple, clean list, with one term, abbreviation, or misspelling per line.
            - Do not include any other text, explanations, or formatting.

            Generate the list now.
        """

        # 4. Generate the dictionary content
        logger.info(
            "Generating medical dictionary content with the LLM... This may take a few minutes."
        )
        dictionary_content = llm_service.generate_analysis(prompt)

        # 5. Save the content to the file
        output_path = "src/resources/medical_dictionary.txt"
        with open(output_path, "w") as f:
            f.write(dictionary_content)

        logger.info(
            f"Successfully generated and saved the expanded medical dictionary to {output_path}"
        )

    except Exception as e:
        logger.error(
            f"An error occurred during dictionary generation: {e}", exc_info=True
        )


if __name__ == "__main__":
    generate_medical_dictionary()
