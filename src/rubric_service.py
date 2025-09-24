import logging
from typing import List, Optional, Dict, Any
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS
from pydantic import BaseModel, Field
import json

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic model for a compliance rule
class ComplianceRule(BaseModel):
    uri: str
    issue_title: str
    issue_detail: str
    severity: str
    strict_severity: Optional[str] = None
    issue_category: str
    discipline: str
    document_type: Optional[str] = None
    suggestion: str
    financial_impact: int
    positive_keywords: List[str] = Field(default_factory=list)
    negative_keywords: List[str] = Field(default_factory=list)

class RubricService:
    """
    A service to manage and query compliance rubrics from a TTL ontology file.
    """
    def __init__(self, ontology_path: str = None):  # Path is now optional
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

        try:
            NS_URI = "http://example.com/speckit/ontology#"
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
            GROUP BY ?rule ?title ?detail ?severity ?strict_severity ?category ?discipline ?document_type ?suggestion ?financial_impact
            """

            results = self.graph.query(query)

            rules = []
            for row in results:
                rule = ComplianceRule(
                    uri=str(row.rule),
                    issue_title=str(row.title) if row.title else "",
                    issue_detail=str(row.detail) if row.detail else "",
                    severity=str(row.severity) if row.severity else "",
                    strict_severity=str(row.strict_severity) if row.strict_severity else "",
                    issue_category=str(row.category) if row.category else "General",
                    discipline=str(row.discipline) if row.discipline else "All",
                    document_type=str(row.document_type) if row.document_type else None,
                    suggestion=str(row.suggestion) if row.suggestion else "No suggestion available.",
                    financial_impact=int(row.financial_impact) if row.financial_impact else 0,
                    positive_keywords=str(row.positive_keywords).split('|') if row.positive_keywords else [],
                    negative_keywords=str(row.negative_keywords).split('|') if row.negative_keywords else []
                )
                rules.append(rule)
            logger.info(f"Successfully retrieved and processed {len(rules)} rules from the ontology.")
            return rules
        except Exception as e:
            logger.exception(f"Failed to query and process rules from ontology: {e}")
            return []

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