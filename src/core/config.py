from pydantic import BaseModel
from pathlib import Path

class CitadelConfig(BaseModel):
    base_dir: Path = Path(__file__).resolve().parents[1]
    jobs_dir: Path = base_dir / "jobs"
    logs_dir: Path = base_dir / "logs"
    log_file: Path = logs_dir / "citadel.log"

    db_url: str = "postgresql://citadel:citadel@localhost:5432/citadel"
    llm_endpoint: str = "http://localhost:11434/api/generate"
    llm_model: str = "llama3"

CONFIG = CitadelConfig()
