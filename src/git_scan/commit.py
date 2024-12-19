"""Module for the Commit class."""

import datetime as dt


class Commit:
    """Class for handling commit objects."""

    def __init__(self, commit_hash: str, tree_hash: str, timestamp: str, timezone: str):
        self.hash = commit_hash
        self.tree_hash = tree_hash

        timezone = self._convert_timezone(timezone)
        self.datetime = dt.datetime.fromtimestamp(int(timestamp), timezone)

    @staticmethod
    def _convert_timezone(offset_str):
        """Concert timezone offset str."""
        hours = int(offset_str[1:3])
        if offset_str.startswith("-"):
            hours = -hours
        minutes = int(offset_str[3:])

        return dt.timezone(dt.timedelta(hours=hours, minutes=minutes))

    def __gt__(self, other):
        return self.datetime > other.datetime

    def __str__(self):
        return self.hash
