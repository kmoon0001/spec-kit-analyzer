import logging
from pathlib import Path
from typing import List

from rdflib import Graph, URIRef
from rdflib.namespace import RDF

from src.core.compliance_types import ComplianceRule


logger = logging.getLogger(__name__)


class RuleLoader:
    """Loads compliance rules from Turtle files."""

    def __init__(self, rule_dir: str) -> None:
        self.rule_dir = Path(rule_dir)

    def load_rules(self) -> List[ComplianceRule]:
        if not self.rule_dir.is_dir():
            raise FileNotFoundError(f"Rules directory not found: {self.rule_dir}")

        rules: List[ComplianceRule] = []
        for path in sorted(self.rule_dir.glob("*.ttl")):
            rules.extend(self._parse_rule_file(path))
        return rules

    def _parse_rule_file(self, filepath: Path) -> List[ComplianceRule]:
        graph = Graph()
        graph.parse(str(filepath), format="turtle")
        namespaces = dict(graph.namespace_manager.namespaces())
        default_ns = namespaces.get("", "")

        rule_class_uri = URIRef(default_ns + "ComplianceRule")
        rules: List[ComplianceRule] = []

        for subject in graph.subjects(RDF.type, rule_class_uri):
            try:
                rules.append(self._create_rule_from_graph(graph, subject, default_ns))
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(
                    "Failed to parse rule %s in %s: %s", subject, filepath, exc
                )
        return rules

    def _create_rule_from_graph(
        self, graph: Graph, rule_uri: URIRef, default_ns: str
    ) -> ComplianceRule:
        def literal(predicate: str) -> str | None:
            value = graph.value(rule_uri, URIRef(default_ns + predicate))
            return value.toPython() if value is not None else None

        def keywords(predicate: str) -> List[str]:
            keyword_list: List[str] = []
            keyword_node = graph.value(rule_uri, URIRef(default_ns + predicate))
            if keyword_node is None:
                return keyword_list
            keyword_predicate = URIRef(default_ns + "hasKeyword")
            for keyword in graph.objects(keyword_node, keyword_predicate):
                keyword_list.append(keyword.toPython())
            return keyword_list

        return ComplianceRule(
            uri=str(rule_uri),
            severity=literal("hasSeverity") or "",
            strict_severity=literal("hasStrictSeverity") or "",
            issue_title=literal("hasIssueTitle") or "",
            issue_detail=literal("hasIssueDetail") or "",
            issue_category=literal("hasIssueCategory") or "",
            discipline=literal("hasDiscipline") or "any",
            document_type=literal("hasDocumentType") or "any",
            suggestion=literal("hasSuggestion") or "",
            financial_impact=int(literal("hasFinancialImpact") or 0),
            positive_keywords=keywords("hasPositiveKeywords"),
            negative_keywords=keywords("hasNegativeKeywords"),
        )
