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
        # The rubrics are designed to be loaded together.
        # We will load all .ttl files from the src directory into one graph.
        import glob
        # The main ontology is in pt_compliance_rubric.ttl, load it first.
        main_ontology = "src/pt_compliance_rubric.ttl"
        other_rubrics = glob.glob("src/*.ttl")
        other_rubrics.remove(main_ontology)

        try:
            self.graph.parse(main_ontology, format="turtle")
            for file_path in other_rubrics:
                self.graph.parse(file_path, format="turtle")
            logger.info(f"Successfully loaded all rubric files.")
        except Exception as e:
            logger.exception(f"Failed to load or parse the rubric ontologies: {e}")

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

rules = []
try:
    NS_URI = "http://example.com/speckit/ontology#"
    query = f"""
        SELECT ?rule ?title ?detail ?severity ?strict_severity ?category ?discipline ?document_type ?suggestion ?financial_impact
               (GROUP_CONCAT(DISTINCT ?pos_kw; SEPARATOR="|") AS ?positive_keywords)
               (GROUP_CONCAT(DISTINCT ?neg_kw; SEPARATOR="|") AS ?negative_keywords)
        WHERE {{
            ?rule a <{NS_URI}ComplianceRule> .
            OPTIONAL {{ ?rule <{NS_URI}hasTitle> ?title . }}
            OPTIONAL {{ ?rule <{NS_URI}hasDetail> ?detail . }}
            OPTIONAL {{ ?rule <{NS_URI}hasSeverity> ?severity . }}
            OPTIONAL {{ ?rule <{NS_URI}hasStrictSeverity> ?strict_severity . }}
            OPTIONAL {{ ?rule <{NS_URI}hasCategory> ?category . }}
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
        }}
        GROUP BY ?rule ?title ?detail ?severity ?strict_severity ?category ?discipline ?document_type ?suggestion ?financial_impact
    """
    results = self.graph.query(query)
    # ...process results as needed...
except Exception as e:
    # ...handle error...

            for row in results:
                # The GROUP_CONCAT returns a single string, so we split it by our separator
                pos_kws = str(row.positive_keywords).split('|') if row.positive_keywords else []
                neg_kws = str(row.negative_keywords).split('|') if row.negative_keywords else []

                rule = ComplianceRule(
                    uri=str(row.rule),
rule = dict(
    severity=str(row.severity) if row.severity else "",
    strict_severity=str(row.strict_severity) if row.strict_severity else "",
    issue_title=str(row.title) if row.title else "",
    issue_detail=str(row.detail) if row.detail else "",
    issue_category=str(row.category) if row.category else "General",
    discipline=str(row.discipline) if row.discipline else "All",
    document_type=str(row.document_type) if hasattr(row, "document_type") and row.document_type else None,
    suggestion=str(row.suggestion) if hasattr(row, "suggestion") and row.suggestion else "No suggestion available.",
    financial_impact=int(row.financial_impact) if row.financial_impact else 0,
    positive_keywords=[kw for kw in pos_kws if kw],
    negative_keywords=[kw for kw in neg_kws if kw]
)
                )
                rules.append(rule)
            logger.info(f"Successfully retrieved {len(rules)} rules from the ontology.")
        except Exception as e:
            logger.exception(f"Failed to query rules from ontology: {e}")

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
