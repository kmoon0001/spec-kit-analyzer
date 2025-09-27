import os
import logging
from typing import List
from rdflib import Graph, URIRef
from rdflib.namespace import RDF
from src.core.models import ComplianceRule

from src.config import get_settings

logger = logging.getLogger(__name__)


class RuleLoader:
    def __init__(self):
        settings = get_settings()
        self.rule_dir = settings.rule_dir
        self.rules: List[Dict[str, Any]] = []
        self._load_rules()

    def load_rules(self) -> List[ComplianceRule]:
        """
        Loads all compliance rules from the .ttl files in the specified directory.
        """
        all_rules = []
        if not os.path.isdir(self.rules_directory):
            logger.warning(f"Rules directory not found: {self.rules_directory}")
            return all_rules

        for filename in os.listdir(self.rules_directory):
            if filename.endswith(".ttl"):
                filepath = os.path.join(self.rules_directory, filename)
                try:
                    all_rules.extend(self._parse_rule_file(filepath))
                    logger.info(f"Successfully loaded rules from: {filepath}")
                except Exception as e:
                    logger.error(f"Failed to parse rule file: {filepath}. Error: {e}")
        return all_rules

    def _parse_rule_file(self, filepath: str) -> List[ComplianceRule]:
        """
        Parses a single .ttl file and returns a list of ComplianceRule objects.
        """
        g = Graph()
        g.parse(filepath, format="turtle")
        rules = []

        # Find all subjects that are of type :ComplianceRule
        ns = dict(g.namespace_manager.namespaces())
        rule_class_uri = URIRef(ns.get("", "") + "ComplianceRule")

        for rule_uri in g.subjects(RDF.type, rule_class_uri):
            try:
                rule = self._create_rule_from_graph(g, rule_uri, ns)
                if rule:
                    rules.append(rule)
            except Exception as e:
                logger.error(f"Failed to create rule from graph for URI: {rule_uri} in file: {filepath}. Error: {e}")
        return rules

    @staticmethod
    def _get_literal(g, subject, predicate_uri):
        """Helper to get a single literal value."""
        value = g.value(subject, predicate_uri)
        return value.toPython() if value else None

    @staticmethod
    def _get_keywords(g, subject, predicate_uri, ns):
        """Helper to get a list of keywords."""
        keywords = []
        keyword_set_uri = g.value(subject, predicate_uri)
        if keyword_set_uri:
            keyword_predicate_uri = URIRef(ns[""] + "hasKeyword")
            for keyword in g.objects(keyword_set_uri, keyword_predicate_uri):
                keywords.append(keyword.toPython())
        return keywords

    def _create_rule_from_graph(
        self, g: Graph, rule_uri: URIRef, ns: dict
    ) -> ComplianceRule:
        """
        Creates a ComplianceRule object from the RDF graph data.
        """
        # Define predicate URIs
        has_severity = URIRef(ns[""] + "hasSeverity")
        has_strict_severity = URIRef(ns[""] + "hasStrictSeverity")
        has_issue_title = URIRef(ns[""] + "hasIssueTitle")
        has_issue_detail = URIRef(ns[""] + "hasIssueDetail")
        has_issue_category = URIRef(ns[""] + "hasIssueCategory")
        has_discipline = URIRef(ns[""] + "hasDiscipline")
        has_document_type = URIRef(ns[""] + "hasDocumentType")
        has_suggestion = URIRef(ns[""] + "hasSuggestion")
        has_financial_impact = URIRef(ns[""] + "hasFinancialImpact")
        has_positive_keywords = URIRef(ns[""] + "hasPositiveKeywords")
        has_negative_keywords = URIRef(ns[""] + "hasNegativeKeywords")

        # Extract data
        severity = self._get_literal(g, rule_uri, has_severity)
        strict_severity = self._get_literal(g, rule_uri, has_strict_severity)
        issue_title = self._get_literal(g, rule_uri, has_issue_title)
        issue_detail = self._get_literal(g, rule_uri, has_issue_detail)
        issue_category = self._get_literal(g, rule_uri, has_issue_category)
        discipline = self._get_literal(g, rule_uri, has_discipline)
        document_type = self._get_literal(g, rule_uri, has_document_type) or "any"
        suggestion = self._get_literal(g, rule_uri, has_suggestion)
        financial_impact_str = self._get_literal(g, rule_uri, has_financial_impact)
        financial_impact = int(financial_impact_str) if financial_impact_str else 0

        positive_keywords = self._get_keywords(g, rule_uri, has_positive_keywords, ns)
        negative_keywords = self._get_keywords(g, rule_uri, has_negative_keywords, ns)

        return ComplianceRule(
            uri=str(rule_uri),
            severity=severity,
            strict_severity=strict_severity,
            issue_title=issue_title,
            issue_detail=issue_detail,
            issue_category=issue_category,
            discipline=discipline,
            document_type=document_type,
            suggestion=suggestion,
            financial_impact=financial_impact,
            positive_keywords=positive_keywords,
            negative_keywords=negative_keywords,
        )
