import unittest
from src.core.rule_loader import RuleLoader
from src.core.domain_models import ComplianceRule


class TestRuleLoader(unittest.TestCase):
    def setUp(self):
        # Use the test .ttl files provided in the tests directory
        self.rules_directory = "tests"
        self.loader = RuleLoader(self.rules_directory)

    def test_load_rules(self):
        """Test that rules are loaded from the .ttl files."""
        rules = self.loader.load_rules()
        self.assertIsInstance(rules, list)
        self.assertGreater(len(rules), 0, "No rules were loaded.")
        self.assertTrue(all(isinstance(rule, ComplianceRule) for rule in rules))

    def test_rule_parsing(self):
        """Test that the attributes of a loaded rule are parsed correctly."""
        rules = self.loader.load_rules()
        # Find a specific rule to inspect, e.g., the SignatureRule from the PT rubric
        signature_rule = next((r for r in rules if "SignatureRule" in r.uri), None)

        self.assertIsNotNone(signature_rule, "SignatureRule not found in loaded rules.")
        self.assertEqual(
            signature_rule.issue_title, "Provider signature/date possibly missing"
        )
        self.assertEqual(signature_rule.discipline, "pt")
        self.assertEqual(signature_rule.severity, "finding")
        self.assertIn("signature", signature_rule.negative_keywords)
        self.assertEqual(len(signature_rule.positive_keywords), 0)

    def test_non_existent_directory(self):
        """Test that loading rules from a non-existent directory raises an error."""
        with self.assertRaises(FileNotFoundError):
            loader = RuleLoader("non_existent_dir")
            loader.load_rules()


if __name__ == "__main__":
    unittest.main()
