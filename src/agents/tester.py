import subprocess
from pathlib import Path
from core.job_models import JobState


class TesterAgent:
    """
    Runs basic validation on the code output:
    - Syntax check (python -m py_compile)
    - Import check
    - Optional: run pytest if tests exist
    """

    def run(self, state: JobState, job_dir: Path) -> JobState:
        errors = []

        # 1. Syntax check: compile every .py file
        for py_file in job_dir.rglob("*.py"):
            try:
                subprocess.check_output(
                    ["python", "-m", "py_compile", str(py_file)],
                    stderr=subprocess.STDOUT,
                )
            except subprocess.CalledProcessError as e:
                errors.append(f"Syntax error in {py_file}:\n{e.output.decode()}")

        # 2. Try to import main module
        try:
            subprocess.check_output(
                ["python", "-c", "import main"],
                cwd=str(job_dir),
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            errors.append(f"Import error:\n{e.output.decode()}")

        # 3. Optional: Run pytest if tests/ folder exists
        tests_dir = job_dir / "tests"
        if tests_dir.exists():
            try:
                subprocess.check_output(
                    ["pytest", "-q"],
                    cwd=str(job_dir),
                    stderr=subprocess.STDOUT,
                )
            except subprocess.CalledProcessError as e:
                errors.append(f"Test failure:\n{e.output.decode()}")

        # Record results
        for step in state.steps:
            if step.step_name == "test":
                if errors:
                    step.status = "failed"
                    step.log = "\n\n".join(errors)
                else:
                    step.status = "completed"
                    step.log = "All checks passed"

                break

        return state
