import typer
from core.orchestrator import CitadelOrchestrator

def register(app: typer.Typer):
    @app.command("new-job")
    def new_job(description: str):
        """
        Create and run a new Citadel job.
        """
        orch = CitadelOrchestrator()
        state = orch.create_job(description)
        final = orch.run_job(state)
        typer.echo(f"Job completed: {final.job.job_id}")
