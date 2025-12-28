"""Web server commands for Carmy CLI."""

import typer
from rich.console import Console

app = typer.Typer(help="Web server management")
console = Console()


@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
) -> None:
    """Start the Carmy web server.

    Launches the FastAPI web interface for Carmy.
    """
    try:
        import uvicorn
    except ImportError:
        console.print("[red]Web dependencies not installed.[/]")
        console.print("Install with: [bold]pip install carmy[web][/]")
        raise typer.Exit(1)

    console.print(f"[bold blue]Carmy[/] web server starting...")
    console.print(f"  URL: [cyan]http://{host}:{port}[/]")
    console.print(f"  Docs: [cyan]http://{host}:{port}/docs[/]")
    console.print(f"  Reload: {'enabled' if reload else 'disabled'}")
    console.print("\nPress [bold]Ctrl+C[/] to stop.\n")

    uvicorn.run(
        "carmy.api.app:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command("check")
def check() -> None:
    """Check if web dependencies are installed."""
    missing = []

    try:
        import fastapi  # noqa: F401
    except ImportError:
        missing.append("fastapi")

    try:
        import uvicorn  # noqa: F401
    except ImportError:
        missing.append("uvicorn")

    try:
        import jinja2  # noqa: F401
    except ImportError:
        missing.append("jinja2")

    if missing:
        console.print("[red]Missing web dependencies:[/]")
        for pkg in missing:
            console.print(f"  - {pkg}")
        console.print("\nInstall with: [bold]pip install carmy[web][/]")
        raise typer.Exit(1)
    else:
        console.print("[green]All web dependencies installed![/]")
