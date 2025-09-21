import os
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# Third-party imports
try:
    import sparknlp
    from sparknlp.base import DocumentAssembler, Pipeline
    from sparknlp.annotator import SentenceDetector, Tokenizer, WordEmbeddingsModel
    from sparknlp_jsl.annotator import MedicalNerModel, NerConverterInternal
    from pyspark.sql import SparkSession
    spark_nlp_installed = True
except ImportError:
    spark_nlp_installed = False
    print("Spark NLP or PySpark is not installed. JSLNERService will not be available.")
    # Define dummy classes to avoid crashing the app if the library is not installed
    class DocumentAssembler: pass
    class SentenceDetector: pass
    class Tokenizer: pass
    class WordEmbeddingsModel: pass
    class MedicalNerModel: pass
    class NerConverterInternal: pass
    class Pipeline: pass


# Local application imports
from .llm_analyzer import NEREntity

logger = logging.getLogger(__name__)

# --- Configuration ---
# A smaller, efficient clinical NER model from John Snow Labs
DEFAULT_JSL_NER_MODEL = "ner_jsl_slim"

class JSLNERService:
    """
    A service for performing Named Entity Recognition (NER) using a
    John Snow Labs for Healthcare model. This is intended as a potential
    replacement for the standard NERService.
    """
    def __init__(self, model_name: str = DEFAULT_JSL_NER_MODEL, license_key: Optional[str] = None, secret: Optional[str] = None):
        """
        Initializes the JSL NER service by starting a Spark NLP session and creating a pipeline.

        Args:
            model_name (str): The name of the JSL NER model to use.
            license_key (str, optional): The John Snow Labs license key. Defaults to env var AWS_ACCESS_KEY_ID.
            secret (str, optional): The John Snow Labs secret. Defaults to env var AWS_SECRET_ACCESS_KEY.
        """
        self.spark: Optional[SparkSession] = None
        self.pipeline: Optional[Any] = None
        self.model_name = model_name

        if not spark_nlp_installed:
            logger.error("Spark NLP is not installed. Cannot initialize JSLNERService.")
            return

        try:
            logger.info("Initializing Spark NLP session for John Snow Labs...")
            # Start the Spark NLP session, authenticating with the provided keys or environment variables
            params = {"spark.driver.memory": "16G", "spark.serializer": "org.apache.spark.serializer.KryoSerializer"}
            self.spark = sparknlp.start(secret=secret, spark_conf=params)

            logger.info(f"Spark NLP session started. Version: {self.spark.version}")
            logger.info(f"Loading JSL NER model: {self.model_name}")

            # Define the Spark NLP pipeline stages
            document_assembler = (
                DocumentAssembler().setInputCol("text").setOutputCol("document")
            )

            sentence_detector = (
                SentenceDetector().setInputCols(["document"]).setOutputCol("sentence")
            )

            tokenizer = Tokenizer().setInputCols(["sentence"]).setOutputCol("token")

            # Using a standard clinical word embeddings model
            word_embeddings = (
                WordEmbeddingsModel.pretrained("embeddings_clinical", "en", "clinical/models")
                .setInputCols(["sentence", "token"])
                .setOutputCol("embeddings")
            )

            # The core JSL NER model
            medical_ner = (
                MedicalNerModel.pretrained(self.model_name, "en", "clinical/models")
                .setInputCols(["sentence", "token", "embeddings"])
                .setOutputCol("ner")
            )

            # Convert NER labels into human-readable chunks
            ner_converter = (
                NerConverterInternal()
                .setInputCols(["sentence", "token", "ner"])
                .setOutputCol("ner_chunk")
            )

            # Create the pipeline from the defined stages
            pipeline = Pipeline(stages=[
                document_assembler,
                sentence_detector,
                tokenizer,
                word_embeddings,
                medical_ner,
                ner_converter,
            ])

            # Create an empty DataFrame to fit the pipeline and create a LightPipeline
            empty_df = self.spark.createDataFrame([[""]]).toDF("text")
            self.pipeline = pipeline.fit(empty_df)
            logger.info("JSL NER pipeline created and fitted successfully.")

        except Exception as e:
            logger.exception(f"Failed to initialize JSLNERService: {e}")
            self.spark = None
            self.pipeline = None

    def is_ready(self) -> bool:
        """Check if the JSL service has been initialized successfully."""
        return self.pipeline is not None

    def extract_entities(self, text: str) -> List[NEREntity]:
        """
        Extracts named entities from a given text using the JSL model.

        Args:
            text (str): The text to analyze.

        Returns:
            List[NEREntity]: A list of found entities, converted to the standard NEREntity format.
        """
        if not self.is_ready() or not self.spark:
            logger.warning("JSL NER service is not ready. Cannot extract entities.")
            return []

        try:
            logger.info(f"Extracting entities with JSL model '{self.model_name}'...")

            # Create a Spark DataFrame from the input text
            data = self.spark.createDataFrame([[text]]).toDF("text")

            # Transform the data using the pipeline
            result = self.pipeline.transform(data)

            # Collect the results and convert them to NEREntity objects
            entities = []
            for row in result.select("ner_chunk").collect():
                for chunk in row.ner_chunk:
                    entities.append(
                        NEREntity(
                            text=chunk.result,
                            label=chunk.metadata['entity'],
                            score=float(chunk.metadata.get('confidence', 0.0)),
                            start=int(chunk.begin),
                            end=int(chunk.end) + 1,  # JSL's end index is inclusive
                            context=chunk.metadata.get('sentence', ''),
                            models=[self.model_name]
                        )
                    )

            logger.info(f"JSL model extracted {len(entities)} entities.")
            return entities

        except Exception as e:
            logger.exception(f"An error occurred during JSL NER extraction: {e}")
            return []

    def stop(self):
        """Stops the Spark session."""
        if self.spark:
            logger.info("Stopping the Spark session.")
            self.spark.stop()
            self.spark = None
