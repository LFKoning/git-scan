"""Module for the DataFile class."""

import pathlib
from dataclasses import dataclass


@dataclass
class DataFile:
    """Class for managing file metadata."""

    name: str
    folder: pathlib.Path
    hash: str

    @property
    def full_path(self):
        """Return full file path"""
        return self.folder / self.name
