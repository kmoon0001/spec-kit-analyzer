class PromptManager:
    def __init__(self, template_path: str):
        with open(template_path, 'r') as f:
            self.template = f.read()

    def build_prompt(self, **kwargs):
        return self.template.format(**kwargs)