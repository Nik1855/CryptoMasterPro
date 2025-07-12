import os
import requests
import subprocess
from .config import Config
from .utils import log_error

config = Config()


class AutoCoder:
    def __init__(self, bot):
        self.bot = bot

    def get_ai_code_suggestion(self, prompt):
        headers = {
            "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are an expert Python developer."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }

        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            if 'choices' in result and result['choices']:
                return result['choices'][0]['message']['content']
            return None
        except Exception as e:
            log_error("AUTO_CODER", f"API error: {e}")
            return None

    def attempt_auto_fix(self, module, error_text):
        prompt = f"""
        Fix the following Python error in module '{module}':
        {error_text}

        Provide:
        1. Complete fixed code for the module
        2. Explanation of changes
        3. Installation commands if needed
        """

        response = self.get_ai_code_suggestion(prompt)
        if not response:
            return False

        try:
            # Extract code block
            start_tag = "```python"
            end_tag = "```"
            start_idx = response.find(start_tag)
            end_idx = response.find(end_tag, start_idx + len(start_tag))

            if start_idx == -1 or end_idx == -1:
                return False

            code = response[start_idx + len(start_tag):end_idx].strip()

            # Write fixed code
            with open(f"{module}.py", "w") as f:
                f.write(code)

            # Run tests
            test_result = subprocess.run(
                ["python", "-m", "pytest", f"{module}_test.py"],
                capture_output=True,
                text=True
            )

            if test_result.returncode == 0:
                return True
            return False
        except Exception as e:
            log_error("AUTO_FIX", f"Implementation error: {e}")
            return False

    def create_feature(self, description):
        prompt = f"""
        Create a new Python module based on:
        {description}

        Provide:
        1. Complete code for the new module
        2. Integration points with existing system
        3. Required dependencies
        """

        response = self.get_ai_code_suggestion(prompt)
        if not response:
            return False

        try:
            # Extract code block
            start_tag = "```python"
            end_tag = "```"
            start_idx = response.find(start_tag)
            end_idx = response.find(end_tag, start_idx + len(start_tag))

            if start_idx == -1 or end_idx == -1:
                return False

            code = response[start_idx + len(start_tag):end_idx].strip()

            # Extract module name
            first_line = code.split('\n')[0]
            if first_line.startswith('class') or first_line.startswith('def'):
                module_name = "new_feature.py"
            else:
                module_name = first_line.split()[-1].replace(':', '') + ".py"

            # Write new module
            with open(module_name, "w") as f:
                f.write(code)

            return True
        except Exception as e:
            log_error("NEW_FEATURE", f"Creation error: {e}")
            return False