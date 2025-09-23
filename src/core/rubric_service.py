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
    financial_impact: int = 0
    positive_keywords: List[str] = field(default_factory=list)
    negative_keywords: List[str] = field(default_factory=list)


class RubricService:
    """
    Service to load and query the compliance rubric ontology.
    """
    def __init__(self, ontology_path: str):
        """
        Initializes the service by loading the ontology.

        Args:
            ontology_path (str): The file path to the ontology (e.g., 'compliance_rubric.ttl').
        """
        self.graph = Graph()
        try:
            self.graph.parse(ontology_path, format="turtle")
            logger.info(f"Successfully loaded rubric ontology from {ontology_path}")
        except Exception as e:
            logger.exception(f"Failed to load or parse the rubric ontology at {ontology_path}: {e}")

    def get_rules(self) -> List[ComplianceRule]:
        """
        Queries the ontology to retrieve all compliance rules.

        Returns:
            List[ComplianceRule]: A list of dataclass objects, each representing a rule.
        """
        if not len(self.graph):
            logger.warning("Ontology graph is empty. Cannot retrieve rules.")
            return []

        # Define our namespace
        NS = Namespace("http://example.com/speckit/ontology#")

        # Prepare a SPARQL query to get all rules and their properties.
        # OPTIONAL blocks are used because not all rules have all properties (e.g., positive_keywords).

        query = prepareQuery("""
            SELECT ?rule ?severity ?strict_severity ?title ?detail ?category ?financial_impact ?discipline
            WHERE {
                ?rule a NS:ComplianceRule .
                ?rule NS:hasSeverity ?severity .
                ?rule NS:hasStrictSeverity ?strict_severity .
                ?rule NS:hasIssueTitle ?title .
                ?rule NS:hasIssueDetail ?detail .
                ?rule NS:hasIssueCategory ?category .
                ?rule NS:hasDiscipline ?discipline .
                OPTIONAL { ?rule NS:hasFinancialImpact ?financial_impact . }
            }
        """, initNs={"NS": NS})

        rules = []
        try:
            results = self.graph.query(query)
            for row in results:
                rule = ComplianceRule(
                    uri=str(row.rule),
                    severity=str(row.severity),
                    strict_severity=str(row.strict_severity),
                    issue_title=str(row.title),
                    issue_detail=str(row.detail),
                    issue_category=str(row.category),
                    financial_impact=int(row.financial_impact) if row.financial_impact else 0,
                    discipline=str(row.discipline),
                    positive_keywords=self._get_keywords(row.rule, NS.hasPositiveKeywords),
                    negative_keywords=self._get_keywords(row.rule, NS.hasNegativeKeywords)
                )
                rules.append(rule)
            logger.info(f"Successfully retrieved {len(rules)} rules from the ontology.")
        except Exception as e:
            logger.exception(f"Failed to query rules from ontology: {e}")

        return rules

    def _get_keywords(self, rule_uri, keyword_property) -> List[str]:
        keywords = []
        for keyword_set in self.graph.objects(rule_uri, keyword_property):
            for keyword in self.graph.objects(keyword_set, Namespace("http://example.com/speckit/ontology#").hasKeyword):
                keywords.append(str(keyword))
        return keywords
