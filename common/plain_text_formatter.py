""" Plain Text Formatter Module. """

import logging
from datetime import datetime
from common.utils import remove_ansi_code_from_text


class PlainTextFormatter(logging.Formatter):
    """
    A custom formatter for plain text log messages.

    Formats log messages as a plain string, removing ANSI escape codes and including
    timestamp and log level.
    """

    def format(self, record):
        """Formats the log record."""
        date_time = datetime.fromtimestamp(record.created)
        date_string = date_time.strftime("%Y-%m-%d %H:%M:%S")
        plain_text = remove_ansi_code_from_text(record.msg)

        return f"{date_string} - {record.levelname} - {plain_text}"
