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
        # The main ontology is in pt_compliance_rubric.ttl, load it first.
        main_ontology = "src/resources/pt_compliance_rubric.ttl"

        try:
            self.graph.parse(main_ontology, format="turtle", encoding="utf-8")
            logger.info(f"Successfully loaded rubric file: {main_ontology}")
        except Exception as e:
            logger.exception(f"Failed to load or parse the rubric ontology: {e}")

    def get_rules(self) -> List[ComplianceRule]:
        """
        Queries the ontology to retrieve all compliance rules.
        """
        if not self.graph:
            logger.warning("Ontology graph is not loaded. Cannot retrieve rules.")
            return []

        # SPARQL query to fetch all rules and their properties
        query = """
        PREFIX ns: <http://example.com/speckit/ontology#>
        SELECT
            ?rule
            ?severity
            ?strict_severity
            ?issue_title
            ?issue_detail
            ?issue_category
            ?discipline
            ?document_type
            ?suggestion
            ?financial_impact
            (GROUP_CONCAT(DISTINCT ?safe_pos_kw; SEPARATOR="|") AS ?positive_keywords)
            (GROUP_CONCAT(DISTINCT ?safe_neg_kw; SEPARATOR="|") AS ?negative_keywords)
        WHERE {
            ?rule a ns:ComplianceRule .
            OPTIONAL { ?rule ns:hasSeverity ?severity . }
            OPTIONAL { ?rule ns:hasStrictSeverity ?strict_severity . }
            OPTIONAL { ?rule ns:hasIssueTitle ?issue_title . }
            OPTIONAL { ?rule ns:hasIssueDetail ?issue_detail . }
            OPTIONAL { ?rule ns:hasIssueCategory ?issue_category . }
            OPTIONAL { ?rule ns:hasDiscipline ?discipline . }
            OPTIONAL { ?rule ns:hasDocumentType ?document_type . }
            OPTIONAL { ?rule ns:hasSuggestion ?suggestion . }
            OPTIONAL { ?rule ns:hasFinancialImpact ?financial_impact . }
            OPTIONAL {
                ?rule ns:hasPositiveKeywords ?pos_ks .
                ?pos_ks ns:hasKeyword ?pos_kw .
            }
            OPTIONAL {
                ?rule ns:hasNegativeKeywords ?neg_ks .
                ?neg_ks ns:hasKeyword ?neg_kw .
            }
            BIND(IF(BOUND(?pos_kw), ?pos_kw, "") AS ?safe_pos_kw)
            BIND(IF(BOUND(?neg_kw), ?neg_kw, "") AS ?safe_neg_kw)
        }
        GROUP BY ?rule ?severity ?strict_severity ?issue_title ?issue_detail ?issue_category ?discipline ?document_type ?suggestion ?financial_impact
        """

        rules = []
        try:
            results = self.graph.query(query)
            for row in results:
                # Split concatenated keywords into a list and filter out empty strings
                positive_keywords = str(row.positive_keywords).split('|') if row.positive_keywords else []
                positive_keywords = [kw for kw in positive_keywords if kw]
                negative_keywords = str(row.negative_keywords).split('|') if row.negative_keywords else []
                negative_keywords = [kw for kw in negative_keywords if kw]

                # Create a ComplianceRule object from the query result
                rule = ComplianceRule(
                    uri=str(row.rule),
                    severity=str(row.severity or ""),
                    strict_severity=str(row.strict_severity or ""),
                    issue_title=str(row.issue_title or ""),
                    issue_detail=str(row.issue_detail or ""),
                    issue_category=str(row.issue_category or "General"),
                    discipline=str(row.discipline or "All"),
                    document_type=str(row.document_type) if row.document_type else None,
                    suggestion=str(row.suggestion or "No suggestion available."),
                    financial_impact=int(row.financial_impact) if row.financial_impact else 0,
                    positive_keywords=positive_keywords,
                    negative_keywords=negative_keywords,
                )
                rules.append(rule)

            logger.info(f"Successfully retrieved and processed {len(rules)} rules from the ontology.")
        except Exception as e:
            logger.exception(f"Failed to query and process rules from ontology: {e}")
            return []

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
