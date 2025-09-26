import os

class PromptManager:
    def __init__(self, template_path: str):
        # Get the absolute path to the project's root directory
        ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        abs_template_path = os.path.join(ROOT_DIR, template_path)
        with open(abs_template_path, 'r') as f:
            self.template = f.read()

    def build_prompt(self, **kwargs):
        return self.template.format(**kwargs)
