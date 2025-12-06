# src/agents/code_writer.py

from pathlib import Path
from core.job_models import JobState
from core.llm_client import call_llm

import json
import re

def llm_failed(text: str) -> bool:
    lower = text.lower()
    failures = [
        "cannot provide",
        "can't provide",
        "not able to",
        "unable to",
        "cannot generate",
        "i'm not able",
        "i am not able",
        "refuse"
    ]
    return any(f in lower for f in failures)


def extract_json_block(text: str) -> str:
    """
    Extracts the first JSON object from the text, handling markdown fences,
    commentary, and extra text that LLMs often wrap around JSON output.
    """
    # Remove Markdown-style code fences
    text = re.sub(r"```(?:json)?", "", text).replace("```", "")

    # Find JSON object boundaries
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No valid JSON object found in LLM output.")

    return text[start:end+1]


def sanitize_json_like_file_map(cleaned: str) -> str:
    """
    Takes a JSON-like string that may contain multiline triple-quoted blocks
    and converts them into valid JSON strings.

    Strategy:
    - Detect values that start with triple quotes.
    - Capture everything until the matching triple quote.
    - Escape newlines and quotes.
    - Replace with a valid JSON string.
    """

    def replace_block(match):
        file_path = match.group(1)
        content = match.group(2)

        # Normalize content
        escaped = (
            content
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
        )

        return f'"{file_path}": "{escaped}"'

    triple_quote_pattern = re.compile(
        r'"([^"]+)":\s*"""\s*(.*?)\s*"""',
        re.DOTALL
    )

    return re.sub(triple_quote_pattern, replace_block, cleaned)


class CodeWriterAgent:
    """
    Converts the Architect's plan.md into actual source code files.

    The architect defines:
    - file layout
    - modules
    - function responsibilities

    The code writer reads the plan and writes the actual implementation.
    """

    def run(self, state: JobState, job_dir: Path) -> JobState:

        plan_path = job_dir / "plan.md"

        if not plan_path.exists():
            raise FileNotFoundError(f"Architect plan missing: {plan_path}")

        plan = plan_path.read_text(encoding="utf-8")

        system_prompt = """
You are a senior software engineer in The Citadel.

Your task is to take an architect's technical plan and generate the code exactly
according to that plan, producing complete, well-documented, production-quality
Python modules.

Rules:
1. Follow the proposed file layout.
2. Generate one file at a time.
3. Write complete, executable Python.
4. Include docstrings and comments.
5. Include all functions, classes, and imports required.
6. If the plan references tests, create test files too.
7. Never collapse modules into a single file unless the architect says so.
8. NEVER output explanations — only the raw code for each file.
        """.strip()

        user_prompt = f"""
Architect Plan:
---------------------------------------------------
{plan}
---------------------------------------------------

Produce the FULL implementation for all modules referenced.
Return your answer as a JSON object where keys = file paths relative to the job folder,
and values = full file contents.

Example return format:
{{
  "sorting_algorithm.py": "<file text>",
  "main.py": "<file text>",
  "tests/test_sorting_algorithm.py": "<file text>"
}}
        """

        llm_response = call_llm(system_prompt, user_prompt)

        # Detect LLM refusal or incomplete response
        if llm_failed(llm_response) or "{" not in llm_response:
            error_path = job_dir / "code_writer_error.md"
            error_path.write_text(
                f"# Code Writer Failure\n\nLLM refused to generate code.\n\nRaw output:\n```\n{llm_response}\n```",
                encoding="utf-8"
            )

            for step in state.steps:
                if step.step_name == "code_write":
                    step.status = "failed"
                    step.log = "LLM refused to generate code (see code_writer_error.md)"

            return state

        # Clean & extract JSON from messy LLM output
        try:
            cleaned = extract_json_block(llm_response)
            cleaned = sanitize_json_like_file_map(cleaned)   # 🔥 fix triple-quote outputs

            files = json.loads(cleaned)
        except Exception as e:
            raise ValueError(
                f"LLM did not return valid clean JSON: {e}\n--- RAW OUTPUT ---\n{llm_response}"
            )

        # Save generated files
        for rel_path, content in files.items():
            abs_path = job_dir / rel_path
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text(content, encoding="utf-8")

        # Update log
        for step in state.steps:
            if step.step_name == "code_write":
                step.log = f"Generated {len(files)} files"

        return state
