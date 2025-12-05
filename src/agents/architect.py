# src/agents/architect.py

from pathlib import Path

from core.job_models import JobState
from core.llm_client import call_llm


class ArchitectAgent:
    """
    Takes a natural language job description and produces a structured
    implementation plan for the other agents to follow.
    """

    def run(self, state: JobState, job_dir: Path) -> JobState:
        job = state.job

        system_prompt = """
You are a senior software architect.

You are part of an internal system called The Citadel that transforms high-level
requests into production-grade software. You think clearly, structurally, and
with best engineering practices.
        """.strip()

        user_prompt = f"""
JOB DESCRIPTION:
{job.description}

TASK:
1. Analyze the request and restate the goal clearly.
2. Propose a clean architecture for the solution.
3. List the main components/modules.
4. For each component, describe:
   - responsibility
   - inputs/outputs
   - key data structures
5. Propose a basic file/folder layout.
6. Outline an implementation sequence (step-by-step).
7. Call out any risks, unknowns, or decisions that should be confirmed.

OUTPUT FORMAT:
Return a well-structured Markdown document with clear headings, e.g.:

# Overview
# Architecture
# Components
# File Layout
# Implementation Steps
# Risks & Notes
        """.strip()

        plan_md = call_llm(system_prompt, user_prompt)

        plan_path = job_dir / "plan.md"
        plan_path.write_text(plan_md, encoding="utf-8")

        # Tag the step log so we know it ran
        for step in state.steps:
            if step.step_name == "plan":
                step.log = f"Architect produced {plan_path.name}"

        return state
