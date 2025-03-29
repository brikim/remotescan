import logging

from common.utils import remove_ansi_code_from_text


class GotifyPlainTextFormatter(logging.Formatter):
    """
    A custom formatter for Gotify log messages.

    Removes ANSI escape codes from log messages to ensure clean text in Gotify notifications.
    """

    def format(self, record) -> str:
        """Formats the log record by removing ANSI escape codes."""
        return remove_ansi_code_from_text(record.msg)
