import os
import unittest
from tempfile import NamedTemporaryFile

from musigree.utils import download_file


class TestUtils(unittest.TestCase):
    def test_download_file(self):
        # GIVEN
        input_url = "https://getsamplefiles.com/download/gzip/sample-1.gz"

        with NamedTemporaryFile(delete=True, delete_on_close=False) as output_file:

            # WHEN
            download_file(input_url, output_file)

            # THEN
            print(f"name: {output_file.file.name}")
            size = os.path.getsize(output_file.file.name)
            print(f"size: {size}")
            self.assertEqual(361444, size)
