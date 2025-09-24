32    """
33    def __init__(self, ontology_path: str = None):  # Path is now optional
34        """
35        Initializes the service by loading all .ttl rubric ontologies from the src directory.
36        """
37        self.graph = Graph()
38        if ontology_path:
39            self.graph.parse(ontology_path, format="turtle", encoding="utf-8")
40            logger.info(f"Successfully loaded rubric file: {ontology_path}")
41        else:
42            main_ontology = "src/resources/pt_compliance_rubric.ttl"
43            try:
44                self.graph.parse(main_ontology, format="turtle", encoding="utf-8")
45                logger.info(f"Successfully loaded rubric file: {main_ontology}")
46            except Exception as e:
47                logger.exception(f"Failed to load or parse the rubric ontology: {e}")
48
49    def get_rules(self) -> List[ComplianceRule]:
50        """
51        Queries the ontology to retrieve all compliance rules.
52        This method now uses a simpler query and processes the results in Python
53        to avoid SPARQL engine inconsistencies with GROUP_CONCAT.
54        """
55        if not len(self.graph):
56            logger.warning("Ontology graph is empty. Cannot retrieve rules.")
57            return []
58
59        try:
60            NS_URI = "http://example.com/speckit/ontology#"
61            query = f"""
62            SELECT ?rule ?title ?detail ?severity ?strict_severity ?category ?discipline ?document_type ?suggestion ?financial_impact
63                   (GROUP_CONCAT(DISTINCT ?safe_pos_kw; SEPARATOR="|") AS ?positive_keywords)
64                   (GROUP_CONCAT(DISTINCT ?safe_neg_kw; SEPARATOR="|") AS ?negative_keywords)
65            WHERE {{
66                ?rule a <{NS_URI}ComplianceRule> .
67                OPTIONAL {{ ?rule <{NS_URI}hasIssueTitle> ?title . }}
68                OPTIONAL {{ ?rule <{NS_URI}hasIssueDetail> ?detail . }}
69                OPTIONAL {{ ?rule <{NS_URI}hasSeverity> ?severity . }}
70                OPTIONAL {{ ?rule <{NS_URI}hasStrictSeverity> ?strict_severity . }}
71                OPTIONAL {{ ?rule <{NS_URI}hasIssueCategory> ?category . }}
72                OPTIONAL {{ ?rule <{NS_URI}hasDiscipline> ?discipline . }}
73                OPTIONAL {{ ?rule <{NS_URI}hasDocumentType> ?document_type . }}
74                OPTIONAL {{ ?rule <{NS_URI}hasSuggestion> ?suggestion . }}
75                OPTIONAL {{ ?rule <{NS_URI}hasFinancialImpact> ?financial_impact . }}
76                OPTIONAL {{
77                    ?rule <{NS_URI}hasPositiveKeywords> ?pos_ks .
78                    ?pos_ks <{NS_URI}hasKeyword> ?pos_kw .
79                }}
80                OPTIONAL {{
81                    ?rule <{NS_URI}hasNegativeKeywords> ?neg_ks .
82                    ?neg_ks <{NS_URI}hasKeyword> ?neg_kw .
83                }}
84                BIND(IF(BOUND(?pos_kw), ?pos_kw, "") AS ?safe_pos_kw)
85                BIND(IF(BOUND(?neg_kw), ?neg_kw, "") AS ?safe_neg_kw)
86            }}
87            GROUP BY ?rule ?title ?detail ?severity ?strict_severity ?category ?discipline ?document_type ?suggestion ?financial_impact
88            """
89
90            results = self.graph.query(query)
91
92            rules = []
93            for row in results:
94                rule = ComplianceRule(
95                    uri=str(row.rule),
96                    issue_title=str(row.title) if row.title else "",
97                    issue_detail=str(row.detail) if row.detail else "",
98                    severity=str(row.severity) if row.severity else "",
99                    strict_severity=str(row.strict_severity) if row.strict_severity else "",
100                    issue_category=str(row.category) if row.category else "General",
101                    discipline=str(row.discipline) if row.discipline else "All",
102                    document_type=str(row.document_type) if row.document_type else None,
103                    suggestion=str(row.suggestion) if row.suggestion else "No suggestion available.",
104                    financial_impact=int(row.financial_impact) if row.financial_impact else 0,
105                    positive_keywords=str(row.positive_keywords).split('|') if row.positive_keywords else [],
106                    negative_keywords=str(row.negative_keywords).split('|') if row.negative_keywords else []
107                )
108                rules.append(rule)
109            logger.info(f"Successfully retrieved and processed {len(rules)} rules from the ontology.")
110            return rules
111        except Exception as e:
112            logger.exception(f"Failed to query and process rules from ontology: {e}")
113            return []
114
115    def get_filtered_rules(self, doc_type: str, discipline: str = "All") -> List[ComplianceRule]:
116        """
117        Retrieves all compliance rules and filters them for a specific document type and discipline.
118
119        Args:
120            doc_type (str): The type of the document (e.g., 'Evaluation', 'Progress Note').
121            discipline (str): The discipline to filter by (e.g., 'pt', 'ot', 'slp', or 'All').
122
123        Returns:
124            List[ComplianceRule]: A list of rules that apply to the given criteria.
125        """
126        all_rules = self.get_rules()
127
128        # Filter by document type
129        if not doc_type or doc_type == "Unknown":
130            doc_type_rules = all_rules
131        else:
132            doc_type_rules = [
133                rule for rule in all_rules
134                if rule.document_type is None or rule.document_type == doc_type
135            ]
136
137        # Filter by discipline
138        if discipline == "All":
139            final_rules = doc_type_rules
140        else:
141            final_rules = [
142                rule for rule in doc_type_rules
143                if rule.discipline.lower() == discipline.lower()
144            ]
145
146        logger.info(f"Filtered {len(all_rules)} rules down to {len(final_rules)} for doc type '{doc_type}' and discipline '{discipline}'.")
147        return final_rules