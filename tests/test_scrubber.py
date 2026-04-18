from pathlib import Path

import piexif
from typer.testing import CliRunner
from PIL import Image
from photo_metadata_scrubber.logic import app, scrub_exif


runner = CliRunner()


def create_test_image(tmp_path: Path, has_gps: bool = True):
    """Create a dummy JPEG with or without GPS info."""
    img_path = tmp_path / "test.jpg"
    img = Image.new("RGB", (100, 100), color="red")

    if has_gps:
        # Create minimal GPS data
        gps_ifd = {
            piexif.GPSIFD.GPSLatitudeRef: "N",
            piexif.GPSIFD.GPSLatitude: ((45, 1), (30, 1), (0, 1)),
            piexif.GPSIFD.GPSLongitudeRef: "W",
            piexif.GPSIFD.GPSLongitude: ((73, 1), (35, 1), (0, 1)),
        }
        exif_dict = {"GPS": gps_ifd}
        exif_bytes = piexif.dump(exif_dict)
        img.save(img_path, exif=exif_bytes)
    else:
        img.save(img_path)

    return img_path


def test_scrub_exif_removes_gps(tmp_path):
    img_path = create_test_image(tmp_path, has_gps=True)

    # Verify GPS exists first
    exif_dict = piexif.load(img_path.as_posix())
    assert "GPS" in exif_dict and exif_dict["GPS"]

    # Scrub
    result = scrub_exif(img_path)
    assert result is True

    # Verify GPS is gone
    exif_dict = piexif.load(img_path.as_posix())
    assert "GPS" not in exif_dict or not exif_dict["GPS"]


def test_scrub_exif_no_gps(tmp_path):
    img_path = create_test_image(tmp_path, has_gps=False)

    # Scrub
    result = scrub_exif(img_path)
    assert result is False


def test_scrub_exif_dry_run(tmp_path):
    img_path = create_test_image(tmp_path, has_gps=True)

    # Scrub with dry run
    result = scrub_exif(img_path, dry_run=True)
    assert result is True

    # Verify GPS still exists
    exif_dict = piexif.load(img_path.as_posix())
    assert "GPS" in exif_dict and exif_dict["GPS"]


def test_scrub_exif_without_any_exif_returns_false(tmp_path):
    img_path = tmp_path / "plain.jpg"
    Image.new("RGB", (50, 50), color="blue").save(img_path)

    result = scrub_exif(img_path, verbose=False)

    assert result is False


def test_scrub_exif_returns_false_on_processing_error(tmp_path):
    missing_path = tmp_path / "missing.jpg"

    result = scrub_exif(missing_path, verbose=False)

    assert result is False


def test_scrub_command_missing_path_exits_nonzero(tmp_path):
    missing = tmp_path / "does-not-exist"

    result = runner.invoke(app, [str(missing)])

    assert result.exit_code == 1


def test_scrub_command_empty_directory_reports_no_photos(tmp_path):
    result = runner.invoke(app, [str(tmp_path)])

    assert result.exit_code == 0


def test_scrub_command_dry_run_counts_matching_files(tmp_path):
    create_test_image(tmp_path, has_gps=True)

    result = runner.invoke(app, [str(tmp_path), "--dry-run"])

    assert result.exit_code == 0
    assert "Would have scrubbed 1 photos" in result.output
