from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from local_first_common.cli import (
    init_config_option,
    dry_run_option,
    resolve_dry_run,
    pipe_option,
)
from local_first_common.tracking import register_tool
from .core import scrub_exif

TOOL_NAME = "photo-metadata-scrubber"
DEFAULTS = {"provider": "ollama", "model": "llama3"}
_TOOL = register_tool(TOOL_NAME)

console = Console(stderr=True)  # Send rich output to stderr
app = typer.Typer(help="Strips privacy-sensitive EXIF location (GPS) data from photos.")


@app.command()
def scrub(
    path: Path = typer.Argument(..., help="File or directory to scrub"),
    dry_run: Annotated[bool, dry_run_option()] = False,
    pipe: Annotated[bool, pipe_option()] = False,
    init_config: Annotated[bool, init_config_option(TOOL_NAME, DEFAULTS)] = False,
):
    """Strip EXIF location data from the specified photo or directory."""
    dry_run = resolve_dry_run(dry_run, False)

    if not path.exists():
        console.print(f"[red]Path does not exist: {path}[/red]")
        raise typer.Exit(1)

    files_to_process = []
    if path.is_file():
        files_to_process.append(path)
    elif path.is_dir():
        for ext in (".jpg", ".jpeg", ".png", ".tiff"):
            files_to_process.extend(path.glob(f"*{ext}"))
            files_to_process.extend(path.glob(f"*{ext.upper()}"))

    if not files_to_process:
        if not pipe:
            console.print(f"No photos found in {path}")
        return

    if not pipe:
        console.print(
            Panel(
                f"Scrubbing GPS data from {len(files_to_process)} photos...",
                title="Photo Metadata Scrubber",
                border_style="cyan",
            )
        )

    scrubbed_count = 0
    for file in files_to_process:
        # Scrub always overwrites the file in place, so the path doesn't change
        if scrub_exif(file, dry_run=dry_run, verbose=not pipe):
            scrubbed_count += 1

        if pipe:
            # Output the path to stdout for the next tool in the pipe
            print(file.absolute())

    if not pipe:
        if not dry_run:
            console.print(
                f"\n[bold green]Done! Scrubbed {scrubbed_count} photos.[/bold green]"
            )
        else:
            console.print(
                f"\n[yellow][dry-run] Would have scrubbed {scrubbed_count} photos.[/yellow]"
            )


if __name__ == "__main__":
    app()
