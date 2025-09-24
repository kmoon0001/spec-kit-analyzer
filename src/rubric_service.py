from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery 

logger = logging.getLogger(__name__)

# Define a dataclass to hold the rule information in a structured way
@dataclass
class ComplianceRule:
    uri: str
    severity: str
    strict_severity: str
    issue_title: str
    issue_detail: str
    issue_category: str
    discipline: str
    document_type: Optional[str] = None
    suggestion: str = ""
    financial_impact: int = 0
    positive_keywords: List[str] = field(default_factory=list)
    negative_keywords: List[str] = field(default_factory=list)


class RubricService:
    """
    Service to load and query the compliance rubric ontology.
    """
    def __init__(self, ontology_path: str = None): # Path is now optional
        """
        Initializes the service by loading all .ttl rubric ontologies from the src directory.
        """
        self.graph = Graph()
        if ontology_path:
            self.graph.parse(ontology_path, format="turtle", encoding="utf-8")
            logger.info(f"Successfully loaded rubric file: {ontology_path}")
        else:
            main_ontology = "src/resources/pt_compliance_rubric.ttl"
            try:
                self.graph.parse(main_ontology, format="turtle", encoding="utf-8")
                logger.info(f"Successfully loaded rubric file: {main_ontology}")
            except Exception as e:
                logger.exception(f"Failed to load or parse the rubric ontology: {e}")

    def get_rules(self) -> List[ComplianceRule]:
        """
        Queries the ontology to retrieve all compliance rules.
        This method now uses a simpler query and processes the results in Python
        to avoid SPARQL engine inconsistencies with GROUP_CONCAT.
        """
        if not len(self.graph):
            logger.warning("Ontology graph is empty. Cannot retrieve rules.")
            return []

        NS_RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
        self.graph.bind("rdfs", NS_RDFS)
        NS = Namespace("http://example.com/ns#")
        self.graph.bind("", NS)
        query = prepareQuery(
            """
            SELECT ?rule ?severity ?strict_severity ?issue_title ?issue_detail ?issue_category ?discipline ?document_type ?suggestion ?financial_impact
            WHERE {
                ?rule a :ComplianceRule .
                OPTIONAL { ?rule :hasSeverity ?severity . }
                OPTIONAL { ?rule :hasStrictSeverity ?strict_severity . }
                OPTIONAL { ?rule :hasIssueTitle ?issue_title . }
                OPTIONAL { ?rule :hasIssueDetail ?issue_detail . }
                OPTIONAL { ?rule :hasIssueCategory ?issue_category . }
                OPTIONAL { ?rule :hasDiscipline ?discipline . }
                OPTIONAL { ?rule :hasDocumentType ?document_type . }
                OPTIONAL { ?rule :hasSuggestion ?suggestion . }
                OPTIONAL { ?rule :hasFinancialImpact ?financial_impact . }
            }
            """,
            initNs={":": NS, "rdfs": NS_RDFS}
        )

        rules = []
        try:
            results = self.graph.query(query)
            for row in results:
                rules.append(ComplianceRule(
                    uri=str(row.rule),
                    severity=str(row.severity),
                    strict_severity=str(row.strict_severity),
                    issue_title=str(row.issue_title),
                    issue_detail=str(row.issue_detail),
                    issue_category=str(row.issue_category),
                    discipline=str(row.discipline),
                    document_type=str(row.document_type) if row.document_type else None,
                    suggestion=str(row.suggestion),
                    financial_impact=int(row.financial_impact) if row.financial_impact else 0
                ))

            logger.info(f"Successfully retrieved and processed {len(rules)} rules from the ontology.")
        except Exception as e:
            logger.exception(f"Failed to query and process rules from ontology: {e}")
            return [] # Return empty list on failure

        return rules

    def get_filtered_rules(self, doc_type: str, discipline: str = "All") -> List[ComplianceRule]:
        """
        Retrieves all compliance rules and filters them for a specific document type and discipline.

        Args:
            doc_type (str): The type of the document (e.g., 'Evaluation', 'Progress Note').
            discipline (str): The discipline to filter by (e.g., 'pt', 'ot', 'slp', or 'All').

        Returns:
            List[ComplianceRule]: A list of rules that apply to the given criteria.
        """
        all_rules = self.get_rules()

        # Filter by document type
        if not doc_type or doc_type == "Unknown":
            doc_type_rules = all_rules
        else:
            doc_type_rules = [
                rule for rule in all_rules
                if rule.document_type is None or rule.document_type == doc_type
            ]

        # Filter by discipline
        if discipline == "All":
            final_rules = doc_type_rules
        else:
            final_rules = [
                rule for rule in doc_type_rules
                if rule.discipline.lower() == discipline.lower()
            ]

        logger.info(f"Filtered {len(all_rules)} rules down to {len(final_rules)} for doc type '{doc_type}' and discipline '{discipline}'.")
        return final_rules
