import typer
from . import new_job

app = typer.Typer(help="The Citadel — AI Software Forge CLI")

# Register subcommands from separate modules
new_job.register(app)

def get_app():
    return app
