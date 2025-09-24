116         query = document_text
117         doc_type_obj = doc_type
118         if self.use_query_transformation:
119             query = self._transform_query(query)
120         retrieved_rules = (
121             self.retriever.search(query=query)
122             if self.retriever
123             else
124             self.guideline_service.search(query=query)
125         )
126         context_str = self._format_rules_for_prompt(retrieved_rules)
127         logger.info("Retrieved and formatted context.")
128
129         prompt = self.prompt_manager.build_prompt(document_text, entities_str, context_str)
130
131         inputs = self.generator_tokenizer(prompt, return_tensors="pt").to(self.generator_model.device)
132         output = self.generator_model.generate(**inputs, max_new_tokens=512, num_return_sequences=1)
133         result = self.generator_tokenizer.decode(output[0], skip_special_tokens=True)
134
135         analysis = self._parse_json_output(result)
136         logger.info("Raw model analysis returned.")
137
138         analysis = self.explanation_engine.generate_explanation(analysis)
139         logger.info("Explanations generated.")
140
141         return analysis
142
143     def _transform_query(self, query: str) -> str:
144         return query
145
146     def _format_rules_for_prompt(self, rules: list) -> str:
147         if not rules:
148             return "No specific compliance rules were retrieved. Analyze based on general Medicare principles."
149         formatted_rules = []
150         for rule in rules:
151             formatted_rules.append(
152                 f"- **Rule:** {rule.get('text', '')}\n"
153                 f"  **Source:** {rule.get('source', '')}\n"
154             )
155         return "\n".join(formatted_rules)
156
157     def _parse_json_output(self, result: str) -> dict:
158         """
159         Parses JSON output from the model with robust error handling.
160         """
161         try:
162             # First try to find JSON wrapped in code blocks
163             json_start = result.find('```json')
164             if json_start != -1:
165                 json_str = result[json_start + 7:].strip()
166                 json_end = json_str.rfind('```')
167                 if json_end != -1:
168                     json_str = json_str[:json_end].strip()
169             else:
170                 # Fall back to finding raw JSON braces
171                 json_start = result.find('{')
172                 json_end = result.rfind('}') + 1
173                 json_str = result[json_start:json_end]
174             
175             analysis = json.loads(json_str)
176             return analysis
177             
178         except (json.JSONDecodeError, IndexError, ValueError) as e:
179             logger.error(f"Error parsing JSON output: {e}\nRaw model output:\n{result}")
180             analysis = {"error": "Failed to parse JSON output from model."}
181             return analysis