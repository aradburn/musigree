"""Integration tests for musigree.utils module."""

import os
from tempfile import NamedTemporaryFile

from musigree.utils import download_file


def test_download_file() -> None:
    """Test downloading a file from a URL to a temporary file.

    This integration test verifies that the download_file function
    can successfully download a sample gzip file from the internet
    and save it to a temporary file with the expected size.
    """
    # GIVEN
    input_url: str = "https://getsamplefiles.com/download/gzip/sample-1.gz"
    expected_size: int = 361444

    with NamedTemporaryFile(delete=True, delete_on_close=False) as output_file:
        # WHEN
        download_file(input_url, output_file)  # type: ignore[arg-type]

        # THEN
        assert output_file.name is not None
        actual_size: int = os.path.getsize(output_file.name)
        assert actual_size == expected_size, (
            f"Expected file size {expected_size}, but got {actual_size}"
        )
