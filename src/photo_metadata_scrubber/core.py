from pathlib import Path

import piexif
from PIL import Image
from rich.console import Console

console = Console(stderr=True)


class PhotoScrubberError(Exception):
    """Base error for scrub-photo core operations."""


class ExifReadError(PhotoScrubberError):
    """Raised when image EXIF data cannot be read."""


class ExifWriteError(PhotoScrubberError):
    """Raised when updated EXIF data cannot be written."""


def scrub_exif_or_raise(
    image_path: Path, dry_run: bool = False, verbose: bool = True
) -> bool:
    """Strict EXIF scrubber that raises typed errors for I/O problems."""
    try:
        img = Image.open(image_path)
    except Exception as e:  # noqa: BLE001
        raise ExifReadError(f"Could not open image {image_path.name}: {e}") from e

    if "exif" not in img.info:
        if verbose:
            console.print(f"[dim]No EXIF data found in {image_path.name}[/dim]")
        return False

    try:
        exif_dict = piexif.load(img.info["exif"])
    except Exception as e:  # noqa: BLE001
        raise ExifReadError(f"Could not parse EXIF for {image_path.name}: {e}") from e

    if not exif_dict.get("GPS"):
        if verbose:
            console.print(f"[dim]No GPS data found in {image_path.name}[/dim]")
        return False

    if dry_run:
        if verbose:
            console.print(
                f"[yellow][dry-run] Would remove GPS tags from {image_path.name}[/yellow]"
            )
        return True

    del exif_dict["GPS"]
    exif_bytes = piexif.dump(exif_dict)

    try:
        img.save(image_path, exif=exif_bytes)
    except Exception as e:  # noqa: BLE001
        raise ExifWriteError(
            f"Could not save updated EXIF for {image_path.name}: {e}"
        ) from e

    if verbose:
        console.print(
            f"[green]Successfully scrubbed GPS data from {image_path.name}[/green]"
        )
    return True


def scrub_exif(image_path: Path, dry_run: bool = False, verbose: bool = True) -> bool:
    """Compatibility wrapper for callers that expect bool status."""
    try:
        return scrub_exif_or_raise(image_path, dry_run=dry_run, verbose=verbose)
    except PhotoScrubberError as e:
        if verbose:
            console.print(f"[red]Error processing {image_path.name}: {e}[/red]")
        return False
