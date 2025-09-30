import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class QualityAssuranceService:
    """
    A service to perform automated checks for clinical accuracy.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.consistency_map = self._load_consistency_map()

    def _load_consistency_map(self) -> Dict[str, List[str]]:
        """
        Loads a map to check for consistency between clinical entities
        and recommendations. In a real application, this would be more
        sophisticated, likely using embeddings or a knowledge graph.
        """
        return {
            "Pain": ["pain", "comfort", "analgesic"],
            "Range of Motion": ["rom", "range of motion", "flexibility", "stretching"],
            "Strength": ["strength", "strengthening", "exercise"],
            "Gait": ["gait", "walking", "ambulation"],
            "Balance": ["balance", "stability"],
            "Activities of Daily Living": ["adl", "dressing", "bathing", "self-care"],
        }

    def check_consistency(
        self,
        entities: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Checks if the recommendations in the findings are consistent with
        the extracted clinical entities.

        Args:
            entities (List[Dict[str, Any]]): A list of extracted and
                                             normalized clinical entities.
            findings (List[Dict[str, Any]]): A list of findings from the
                                             compliance analysis.

        Returns:
            List[Dict[str, Any]]: A list of consistency issues.
        """
        consistency_issues = []
        normalized_entities = {e["normalized_term"] for e in entities}

        for entity in normalized_entities:
            if entity in self.consistency_map:
                is_addressed = False
                for finding in findings:
                    recommendation = finding.get("suggestion", "").lower()
                    for keyword in self.consistency_map[entity]:
                        if keyword in recommendation:
                            is_addressed = True
                            break
                    if is_addressed:
                        break

                if not is_addressed:
                    consistency_issues.append({
                        "entity": entity,
                        "issue": f"The clinical finding '{entity}' was identified, but no related recommendation was found.",
                    })

        return consistency_issues