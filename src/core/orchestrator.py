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

        steps = [
            JobStep(step_name="plan", agent="architect", status="pending"),
            JobStep(step_name="code_write", agent="code_writer", status="pending"),
            JobStep(step_name="test", agent="tester", status="pending"),
        ]

        state = JobState(job=job, steps=steps)

        job_dir = self.jobs_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        (job_dir / "request.json").write_text(
            job.model_dump_json(indent=2), encoding="utf-8"
        )

        return state

    def run_job(self, state: JobState):
        job_dir = self.jobs_dir / state.job.job_id

        for step in state.steps:

            # ARCHITECT AGENT
            if step.agent == "architect":
                from agents.architect import ArchitectAgent
                agent = ArchitectAgent()

                step.started_at = datetime.utcnow()
                step.status = "running"

                state = agent.run(state, job_dir)

                step.status = "completed"
                step.finished_at = datetime.utcnow()

            # CODE WRITER AGENT
            elif step.agent == "code_writer":
                from agents.code_writer import CodeWriterAgent
                agent = CodeWriterAgent()

                step.started_at = datetime.utcnow()
                step.status = "running"

                state = agent.run(state, job_dir)

                step.status = "completed"
                step.finished_at = datetime.utcnow()

            # TESTER AGENT  ← **NEW BLOCK**
            elif step.agent == "tester":
                from agents.tester import TesterAgent
                agent = TesterAgent()

                step.started_at = datetime.utcnow()
                step.status = "running"

                state = agent.run(state, job_dir)

                # TesterAgent itself should update success/failure in step.log
                step.status = "completed"
                step.finished_at = datetime.utcnow()

            # UNKNOWN AGENT — fail safely
            else:
                step.status = "failed"
                step.log = f"Unknown agent type: {step.agent}"

        # Save final job state
        (job_dir / "job_state.json").write_text(
            state.model_dump_json(indent=2),
            encoding="utf-8"
        )

        return state


