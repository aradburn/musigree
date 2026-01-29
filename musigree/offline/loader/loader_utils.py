"""
This module provides utility functions for the data loading process in the Musigree offline system.

It defines the `LoaderUtils` class, which offers a collection of static
methods for handling common tasks related to data loading, such as:
    - **Finding XML file paths**: Locating Discogs XML dump files based on
      the data directory, date, and dump type.
    - **Finding Role paths**: Locating Role files (csv).
    - **Creating XML iterators**: Generating iterators for efficient parsing
      of XML files, including cleaning up the XML elements.
    - **Path Management**: Manages file paths using `os.path.join` and `glob`.
    - **Logging**: Provides logging information for debugging and tracking
      the progress of file operations.

Key functionalities include:
    - **`get_xml_path`**: This method constructs the full path to a Discogs
      XML dump file based on the provided data directory, XML tag (e.g.,
      "artists", "releases"), and date. It uses `glob` to find the most recent
      file matching the pattern, handles date-based and test-data file names.
    - **`get_role_paths`**: This method gets a list of role file path from the
    ROLE_DIR, it returns all .csv files.
    - **`get_iterator`**: This method creates an iterator for parsing a
      Discogs XML dump file. It opens the gzipped XML file, uses
      `ParserUtils.iterparse` to iterate over specific XML elements, and
      then cleans the elements using `ParserUtils.clean_elements`.
    - **Path Handling**: The class uses `os.path.join` to correctly construct
      file paths across different operating systems.
    - **Error Handling**: The code implicitly handles cases where files might
      not be found by using `glob`, which returns an empty list if no files
      match the pattern.
    - **Logging**: The class uses `logging` to provide detailed information
      about the file paths being accessed.

The `LoaderUtils` class interacts with the following components:
    - `musigree.config`: For accessing configuration settings like `ROLE_DIR`.
    - `musigree.offline.loader.parser_utils.ParserUtils`: For parsing
      and cleaning XML elements.
    - `logging`: For logging operations.
    - `os`: For file system operations.
    - `glob`: For file name pattern matching.
    - `gzip`: for opening compressed files

The module utilizes `logging` for logging operations, `os` for file system
operations, `glob` for file pattern matching, `gzip` for reading
compressed files, and `typing` for type hinting.
"""

import glob
import gzip
import logging
import os
from collections.abc import Iterator
from pathlib import Path

from musigree.offline.loader.parser_utils import ParserUtils

log = logging.getLogger(__name__)
"""
The logger for the LoaderUtils module.
"""


class LoaderUtils:
    """
    Provides utility functions for the data loading process.

    This class offers static methods for handling common tasks related to data
    loading, such as finding XML file paths, creating iterators, and managing
    file paths.
    """

    # PUBLIC STATIC METHODS

    @staticmethod
    def get_xml_path(discogs_data_directory: Path, tag: str, date: str = "") -> str:
        """
        Constructs the full path to a Discogs XML dump file.

        This method takes the data directory, XML tag (e.g., "artists",
        "releases"), and date as input and returns the full path to the
        corresponding XML dump file. It uses `glob` to find the most recent
        file matching the pattern.

        Args:
            discogs_data_directory (str): The directory containing the XML files.
            tag (str): The XML tag representing the dump type (e.g., "artist", "release").
            date (str, optional): The date of the dump in YYYYMMDD format.
                Defaults to "".

        Returns:
            str: The full path to the XML dump file.
        """
        glob_pattern = f"discogs_{date}_{tag}s.xml.gz"
        """Create the glob pattern for matching the file."""
        log.info(f"discogs_data_directory: {discogs_data_directory}")
        """Log the data directory."""
        log.info(f"glob_pattern: {glob_pattern}")
        """Log the glob pattern."""
        files = sorted(glob.glob(glob_pattern, root_dir=discogs_data_directory))
        """Find all matching files using glob and sort them."""
        log.info(f"files: {files}")
        """Log the found files."""
        full_path_files = os.path.join(discogs_data_directory, files[-1])
        """Construct the full path to the most recent file."""
        log.info(f"full_path_files: {full_path_files}")
        """Log the full path."""
        return full_path_files

    @staticmethod
    def get_role_paths(roles_directory: Path) -> list[str]:
        """
        Gets a list of paths to role CSV files.

        This method returns a list of full paths to all CSV files in the
        `ROLE_DIR` directory.

        Returns:
            List[str]: A list of full paths to role CSV files.
        """
        glob_pattern = "*.csv"
        """Set the glob pattern to match CSV files."""
        log.debug(f"roles_directory: {roles_directory}")
        """Log the data directory."""
        log.debug(f"glob_pattern: {glob_pattern}")
        """Log the glob pattern."""
        files = sorted(glob.glob(glob_pattern, root_dir=roles_directory))
        """Find all matching files using glob and sort them."""
        log.debug(f"files: {files}")
        """Log the found files."""
        full_path_files = [os.path.join(roles_directory, file) for file in files]
        """Construct the full paths to each file."""
        log.debug(f"full_path_files: {full_path_files}")
        """Log the full paths."""
        return full_path_files

    @staticmethod
    def get_iterator(discogs_data_directory: Path, tag: str, date: str) -> Iterator:
        """
        Creates an iterator for parsing a Discogs XML dump file.

        This method returns an iterator that yields cleaned XML elements from
        a Discogs XML dump file.

        Args:
            discogs_data_directory (Path): The directory containing the XML files.
            tag (str): The XML tag representing the dump type (e.g., "artist", "release").
            date (str): The date of the dump in YYYYMMDD format.

        Returns:
            iterator: An iterator over the cleaned XML elements.
        """
        file_path = LoaderUtils.get_xml_path(discogs_data_directory, tag, date)
        """Get the full path to the XML file."""
        file_pointer = gzip.GzipFile(file_path, "r")
        """Open the XML file using gzip to read compressed files."""
        iterator = ParserUtils.iterparse(file_pointer, tag)
        """Get an iterator over the XML elements with the specified tag."""
        iterator = ParserUtils.clean_elements(iterator)
        """Clean the XML elements."""
        return iterator
