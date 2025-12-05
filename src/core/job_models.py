from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime

JobStatus = Literal["pending", "running", "failed", "completed"]

class JobRequest(BaseModel):
    job_id: str
    description: str
    created_at: datetime

class JobStep(BaseModel):
    step_name: str
    agent: str
    status: JobStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    log: Optional[str] = None

class JobState(BaseModel):
    job: JobRequest
    steps: List[JobStep]
