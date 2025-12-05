from pathlib import Path
from core.job_models import JobState
from core.llm_client import call_llm

SYSTEM_PROMPT = """
You are The Citadel's Code Writer.
You write clean, efficient, readable code with clear structure.
Produce only code or file content, nothing else.
"""

class CodeWriterAgent:
    name = "code_writer"

    def run(self, job_state: JobState, job_dir: Path) -> JobState:
        description = job_state.job.description

        user_prompt = f"""
The task is: {description}

Provide the full code solution.
If multiple files are needed, clearly label sections.
"""

        result = call_llm(SYSTEM_PROMPT, user_prompt)

        repo_dir = job_dir / "repo"
        repo_dir.mkdir(parents=True, exist_ok=True)

        (repo_dir / "output.txt").write_text(result, encoding="utf-8")

        return job_state
