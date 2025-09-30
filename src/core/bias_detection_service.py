import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class BiasDetectionService:
    """
    A service to audit therapeutic recommendations for potential biases.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bias_keywords = self._load_bias_keywords()

    def _load_bias_keywords(self) -> Dict[str, List[str]]:
        """
        Loads keywords associated with potential biases. In a real application,
        this would be a more comprehensive and nuanced list.
        """
        return {
            "age": ["elderly", "young", "old"],
            "gender": ["man", "woman", "male", "female"],
            "socioeconomic": ["poor", "rich", "unemployed"],
        }

    def detect_bias(self, analysis_findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detects potential bias in the recommendations of analysis findings.

        Args:
            analysis_findings (List[Dict[str, Any]]): A list of findings from the
                                                      compliance analysis.

        Returns:
            List[Dict[str, Any]]: A list of findings that may contain biased
                                  language in their recommendations.
        """
        biased_findings = []
        for finding in analysis_findings:
            recommendation = finding.get("suggestion", "").lower()
            for bias_type, keywords in self.bias_keywords.items():
                for keyword in keywords:
                    if keyword in recommendation:
                        biased_findings.append({
                            "finding": finding,
                            "bias_type": bias_type,
                            "keyword": keyword,
                        })
                        # Move to the next finding once a bias is detected
                        break
                else:
                    continue
                break
        return biased_findings