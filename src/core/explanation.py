class ExplanationEngine:
    def add_explanations(self, analysis: dict):
        # This is a placeholder for a more sophisticated explanation engine.
        for finding in analysis.get("findings", []):
            finding["explanation"] = f"This finding was identified because the text '{finding['text']}' triggered a compliance rule related to '{finding['risk']}'."
        return analysis