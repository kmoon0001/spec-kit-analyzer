44 raise RuntimeError(f"Could not load LLM model: {e}") from e
45
46 def is_ready(self) -> bool:
47 """
48         Checks if the model was loaded successfully.
49         """
50 return self.llm is not None
51
52 def generate_analysis(self, prompt: str) -> str:
53 """
54         Generates a response by running the prompt through the loaded LLM.
55         """
56 if self.llm is None:
57 logger.error("LLM is not available. Cannot generate analysis.")
58 return '{"error": "LLM not available"}'
59
60 logger.info("Generating response with the LLM...")
61 try:
62 # Pass the generation parameters directly to the model call
63 raw_text = self.llm(prompt, **self.generation_params)
64 logger.info("LLM response generated successfully.")
65 return raw_text
66 except Exception as e:
67 logger.error(f"Error during LLM generation: {e}", exc_info=True)
68 return f'{{"error": "Failed to generate analysis: {e}"}}'
69
70 def generate_personalized_tip(self, finding: Dict[str, Any]) -> str:
71 """
72         Generates a personalized tip for a specific compliance finding.
73         """
74 if self.llm is None:
75 logger.error("LLM is not available. Cannot generate tip.")
76 return "LLM not available."
77
78 prompt_template = """
79         Given the following compliance issue found in a clinical document, provide a concise, actionable tip for the therapist to improve their documentation.
80         The user is a Physical, Occupational, or Speech Therapist. The tip should be professional, helpful, and directly related to the finding.
81
82         Finding Title: "{title}"
83         Finding Description: "{description}"
84         Relevant quote from document: "{text}"
85
86         Personalized Tip:
87         """
88 prompt = prompt_template.format(
89 title=finding.get('title', 'N/A'),
90 description=finding.get('description', 'N/A'),
91 text=finding.get('text', 'N/A')
92         )
93
94 logger.info(f"Generating personalized tip for finding: {finding.get('title')}")
95 try:
96 tip = self.llm(prompt, **self.generation_params)
97 logger.info("Personalized tip generated successfully.")
98 return tip.strip()
99 except Exception as e:
100 logger.error(f"Error during tip generation: {e}", exc_info=True)
101 return "Could not generate a tip due to an internal error."
102