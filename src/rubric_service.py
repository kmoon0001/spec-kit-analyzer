from __future__ import annotations

import logging
import json
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)

@dataclass
class ComplianceRule:
    uri: str
    severity: str
    strict_severity: str
    issue_title: str
    issue_detail: str
    issue_category: str
    positive_keywords: List[str] = field(default_factory=list)
    negative_keywords: List[str] = field(default_factory=list)


class RubricService:
    """
    Service to load compliance rules from a JSON file.
    """
    def __init__(self, json_path: str):
        """
        Initializes the service.

        Args:
            json_path (str): The file path to the JSON rubric file.
        """
        self.json_path = json_path
        logger.debug(f"RubricService initialized for {json_path}")

    def get_rules(self) -> List[ComplianceRule]:
        """
        Loads and parses the JSON file to retrieve all compliance rules.

        Returns:
            List[ComplianceRule]: A list of dataclass objects, each representing a rule.
        """
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            rules = [ComplianceRule(**rule_data) for rule_data in data]

            logger.info(f"Successfully loaded {len(rules)} rules from {self.json_path}")
            return rules
        except FileNotFoundError:
            logger.error(f"Rubric file not found: {self.json_path}")
            return []
        except json.JSONDecodeError:
            logger.exception(f"Failed to parse JSON from {self.json_path}")
            return []
        except TypeError as e: # Catches errors if JSON structure doesn't match dataclass
            logger.exception(f"Mismatched data in {self.json_path}: {e}")
            return []
        except Exception:
            logger.exception(f"An unexpected error occurred loading rules from {self.json_path}")
            return []
