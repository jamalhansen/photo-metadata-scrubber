from pathlib import Path
from typing import Annotated

import piexif
import typer
from PIL import Image
from rich.console import Console
from rich.panel import Panel

from local_first_common.cli import (
    dry_run_option,
    resolve_dry_run,
)
from local_first_common.tracking import register_tool

_TOOL = register_tool("photo-metadata-scrubber")
console = Console()
app = typer.Typer(help="Strips privacy-sensitive EXIF location (GPS) data from photos.")

def scrub_exif(image_path: Path, dry_run: bool = False) -> bool:
    """Remove GPS info from EXIF data while keeping other tags."""
    try:
        img = Image.open(image_path)
        if "exif" not in img.info:
            if not dry_run:
                console.print(f"[dim]No EXIF data found in {image_path.name}[/dim]")
            return False

        exif_dict = piexif.load(img.info["exif"])
        
        # Check if GPS data exists
        if not exif_dict.get("GPS"):
            if not dry_run:
                console.print(f"[dim]No GPS data found in {image_path.name}[/dim]")
            return False

        if dry_run:
            console.print(f"[yellow][dry-run] Would remove GPS tags from {image_path.name}[/yellow]")
            return True

        # Remove GPS data
        del exif_dict["GPS"]
        exif_bytes = piexif.dump(exif_dict)
        
        # Save without GPS
        img.save(image_path, exif=exif_bytes)
        console.print(f"[green]Successfully scrubbed GPS data from {image_path.name}[/green]")
        return True

    except Exception as e:
        console.print(f"[red]Error processing {image_path.name}: {e}[/red]")
        return False

@app.command()
def scrub(
    path: Annotated[Path, typer.Argument(help="File or directory to scrub")],
    dry_run: Annotated[bool, dry_run_option()] = False,
):
    """Strip EXIF location data from the specified photo or directory."""
    dry_run = resolve_dry_run(dry_run, False)  # no_llm is always False here

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
        console.print(f"No photos found in {path}")
        return

    console.print(Panel(f"Scrubbing GPS data from {len(files_to_process)} photos...", title="Photo Metadata Scrubber", border_style="cyan"))

    scrubbed_count = 0
    for file in files_to_process:
        if scrub_exif(file, dry_run=dry_run):
            scrubbed_count += 1

    if not dry_run:
        console.print(f"\n[bold green]Done! Scrubbed {scrubbed_count} photos.[/bold green]")
    else:
        console.print(f"\n[yellow][dry-run] Would have scrubbed {scrubbed_count} photos.[/yellow]")

if __name__ == "__main__":
    app()
