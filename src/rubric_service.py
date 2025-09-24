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
        This method now uses a simpler query and processes the results in Python
        to avoid SPARQL engine inconsistencies with GROUP_CONCAT.
        """
        if not len(self.graph):
            logger.warning("Ontology graph is empty. Cannot retrieve rules.")
            return []

        NS_URI = "http://example.com/speckit/ontology#"
        # A simpler query to get all rule properties.
        query = f"""
            SELECT ?rule ?title ?detail ?severity ?strict_severity ?category ?discipline ?document_type ?suggestion ?financial_impact
                   (GROUP_CONCAT(DISTINCT ?safe_pos_kw; SEPARATOR="|") AS ?positive_keywords)
                   (GROUP_CONCAT(DISTINCT ?safe_neg_kw; SEPARATOR="|") AS ?negative_keywords)
            WHERE {{
                ?rule a <{NS_URI}ComplianceRule> .
                OPTIONAL {{ ?rule <{NS_URI}hasIssueTitle> ?title . }}
                OPTIONAL {{ ?rule <{NS_URI}hasIssueDetail> ?detail . }}
                OPTIONAL {{ ?rule <{NS_URI}hasSeverity> ?severity . }}
                OPTIONAL {{ ?rule <{NS_URI}hasStrictSeverity> ?strict_severity . }}
                OPTIONAL {{ ?rule <{NS_URI}hasIssueCategory> ?category . }}
                OPTIONAL {{ ?rule <{NS_URI}hasDiscipline> ?discipline . }}
                OPTIONAL {{ ?rule <{NS_URI}hasDocumentType> ?document_type . }}
                OPTIONAL {{ ?rule <{NS_URI}hasSuggestion> ?suggestion . }}
                OPTIONAL {{ ?rule <{NS_URI}hasFinancialImpact> ?financial_impact . }}
                OPTIONAL {{
                    ?rule <{NS_URI}hasPositiveKeywords> ?pos_ks .
                    ?pos_ks <{NS_URI}hasKeyword> ?pos_kw .
                }}
                OPTIONAL {{
                    ?rule <{NS_URI}hasNegativeKeywords> ?neg_ks .
                    ?neg_ks <{NS_URI}hasKeyword> ?neg_kw .
                }}
                BIND(IF(BOUND(?pos_kw), ?pos_kw, "") AS ?safe_pos_kw)
                BIND(IF(BOUND(?neg_kw), ?neg_kw, "") AS ?safe_neg_kw)
            }}
        """

        rules_data = {}
        try:
            results = self.graph.query(query)
            for row in results:
                rule_uri = str(row.rule)
                if rule_uri not in rules_data:
                    rules_data[rule_uri] = {"uri": rule_uri, "positive_keywords": [], "negative_keywords": []}

                prop = str(row.p).replace(NS_URI, "")
                obj = str(row.o)

                if prop == "hasIssueTitle":
                    rules_data[rule_uri]["issue_title"] = obj
                elif prop == "hasIssueDetail":
                    rules_data[rule_uri]["issue_detail"] = obj
                elif prop == "hasSeverity":
                    rules_data[rule_uri]["severity"] = obj
                elif prop == "hasStrictSeverity":
                    rules_data[rule_uri]["strict_severity"] = obj
                elif prop == "hasIssueCategory":
                    rules_data[rule_uri]["issue_category"] = obj
                elif prop == "hasDiscipline":
                    rules_data[rule_uri]["discipline"] = obj
                elif prop == "hasDocumentType":
                    rules_data[rule_uri]["document_type"] = obj
                elif prop == "hasSuggestion":
                    rules_data[rule_uri]["suggestion"] = obj
                elif prop == "hasFinancialImpact":
                    rules_data[rule_uri]["financial_impact"] = int(obj)
                elif prop == "hasPositiveKeywords":
                    # This gives the BNode for the keyword set, need to query for the keywords
                    keyword_query = f"SELECT ?kw WHERE {{ <{obj}> <{NS_URI}hasKeyword> ?kw . }}"
                    for kw_row in self.graph.query(keyword_query):
                        rules_data[rule_uri]["positive_keywords"].append(str(kw_row.kw))
                elif prop == "hasNegativeKeywords":
                    keyword_query = f"SELECT ?kw WHERE {{ <{obj}> <{NS_URI}hasKeyword> ?kw . }}"
                    for kw_row in self.graph.query(keyword_query):
                        rules_data[rule_uri]["negative_keywords"].append(str(kw_row.kw))

            rules = []
            for uri, data in rules_data.items():
                rule = ComplianceRule(
                    uri=uri,
                    severity=data.get("severity", ""),
                    strict_severity=data.get("strict_severity", ""),
                    issue_title=data.get("issue_title", ""),
                    issue_detail=data.get("issue_detail", ""),
                    issue_category=data.get("issue_category", "General"),
                    discipline=data.get("discipline", "All"),
                    document_type=data.get("document_type"),
                    suggestion=data.get("suggestion", "No suggestion available."),
                    financial_impact=data.get("financial_impact", 0),
                    positive_keywords=data.get("positive_keywords", []),
                    negative_keywords=data.get("negative_keywords", [])
                )
                rules.append(rule)

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
