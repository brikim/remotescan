import logging
from common.utils import remove_ansi_code_from_text

# Plain text formatter removes ansi codes for logging
class GotifyPlainTextFormatter(logging.Formatter):
    def format(self, record):
        return remove_ansi_code_from_text(record.msg)
