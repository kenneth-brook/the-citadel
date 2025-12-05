# src/core/orchestrator.py

import uuid
from datetime import datetime
from pathlib import Path

from core.job_models import JobRequest, JobState, JobStep
from core.config import CONFIG
from agents.code_writer import CodeWriterAgent
from agents.architect import ArchitectAgent


class CitadelOrchestrator:
    def __init__(self):
        self.jobs_dir: Path = CONFIG.jobs_dir
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def create_job(self, description: str) -> JobState:
        job_id = str(uuid.uuid4())
        job = JobRequest(
            job_id=job_id,
            description=description,
            created_at=datetime.utcnow(),
        )

        # 🔥 Pipeline v2: Architect -> Code Writer
        steps = [
            JobStep(step_name="plan", agent="architect", status="pending"),
            JobStep(step_name="code_write", agent="code_writer", status="pending"),
        ]

        state = JobState(job=job, steps=steps)

        job_dir = self.jobs_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        (job_dir / "request.json").write_text(
            job.model_dump_json(indent=2), encoding="utf-8"
        )

        return state

    def run_job(self, state: JobState) -> JobState:
        job_dir = self.jobs_dir / state.job.job_id

        for step in state.steps:
            if step.status == "completed":
                continue

            step.started_at = datetime.utcnow()
            step.status = "running"

            if step.agent == "architect":
                agent = ArchitectAgent()
                state = agent.run(state, job_dir)

            elif step.agent == "code_writer":
                agent = CodeWriterAgent()
                state = agent.run(state, job_dir)

            else:
                # Unknown agent – mark as failed but don't crash the whole job
                step.status = "failed"
                step.finished_at = datetime.utcnow()
                step.log = f"Unknown agent: {step.agent}"
                continue

            step.status = "completed"
            step.finished_at = datetime.utcnow()

        (job_dir / "job_state.json").write_text(
            state.model_dump_json(indent=2), encoding="utf-8"
        )

        return state
