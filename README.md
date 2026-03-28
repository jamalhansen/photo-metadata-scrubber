# Photo Metadata Scrubber

Strips privacy-sensitive EXIF location (GPS) data from photos before using them in the blog or newsletter.

## Features

- Strips GPS fields from EXIF data while preserving other tags (camera model, date, etc.).
- Supports single files or entire directories.
- Privacy hygiene: ensuring no location metadata is uploaded.
- Fast, local processing with `Pillow` and `piexif`.

## Usage

```bash
# Scrub a single photo
uv run scrub-photo photo.jpg

# Scrub all photos in a directory
uv run scrub-photo ./photos/

# Dry run (show what would be removed without touching files)
uv run scrub-photo photo.jpg --dry-run
```

## Development

```bash
# Run tests
uv run pytest
```

## Part of the Photo Pipeline
`photo-renamer` → `photo-metadata-scrubber` → `photo-scaler` → `unsplash-uploader`
