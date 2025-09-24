import logging
from typing import List, Dict, Set
from .rubric_service import RubricService, ComplianceRule
import re

logger = logging.getLogger(__name__)

class GraphRetriever:
    """
    Retrieves compliance rules from the knowledge graph based on entities.
    """
    def __init__(self):
        logger.info("Initializing Graph Retriever...")
        self.rubric_service = RubricService()
        self.rules = {rule.uri: rule for rule in self.rubric_service.get_rules()}
        self._build_inverted_index()
        logger.info(f"Loaded and indexed {len(self.rules)} rules into the graph retriever.")
        logger.info("Graph Retriever initialized successfully.")

    def _build_inverted_index(self):
        """
        Builds an inverted index from the rule text to speed up search.
        """
        self.inverted_index: Dict[str, Set[str]] = {}
        for uri, rule in self.rules.items():
            # Combine all text fields from the rule
            text_to_index = " ".join([
                rule.issue_title,
                rule.issue_detail,
            ] + rule.positive_keywords).lower()

            # Simple tokenization by splitting on non-alphanumeric characters
            tokens = set(re.split(r'\W+', text_to_index))

            for token in tokens:
                if token: # Avoid empty strings
                    if token not in self.inverted_index:
                        self.inverted_index[token] = set()
                    self.inverted_index[token].add(uri)

    def search(self, entities: List[str]) -> List[ComplianceRule]:
        """
        Searches for compliance rules that match the given entities using the inverted index.
        :param entities: A list of entity strings extracted from the document.
        :return: A list of matching ComplianceRule objects.
        """
        if not entities:
            return []

        logger.info(f"Searching for rules matching entities: {entities}")

        matching_rule_uris: Set[str] = set()

        for entity in entities:
            # Also search for the tokens within the entity
            entity_tokens = re.split(r'\W+', entity.lower())
            for token in entity_tokens:
                if token in self.inverted_index:
                    matching_rule_uris.update(self.inverted_index[token])

        # Retrieve the full rule objects from the matched URIs
        matching_rules = [self.rules[uri] for uri in matching_rule_uris if uri in self.rules]

        logger.info(f"Found {len(matching_rules)} matching rules from the graph.")
        return matching_rules

if __name__ == '__main__':
    # Example usage:
    graph_retriever = GraphRetriever()

    # Example entities extracted from a document
    example_entities = ["gait training", "skilled nursing facility"]

    # Search for matching rules
    found_rules = graph_retriever.search(example_entities)

    # Print the results
    print(f"\n--- Found {len(found_rules)} Matching Rules ---")
    for rule in found_rules:
        print(f"Rule: {rule.issue_title}")
        print(f"  - Severity: {rule.severity}")
        print(f"  - Detail: {rule.issue_detail}")
        print(f"  - Suggestion: {rule.suggestion}\n")
