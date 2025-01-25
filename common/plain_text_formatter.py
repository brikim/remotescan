import logging
from datetime import datetime
from common.utils import remove_ansi_code_from_text

# Plain text formatter removes ansi codes for logging
class PlainTextFormatter(logging.Formatter):
    def format(self, record):
        date_time = datetime.fromtimestamp(record.created)
        date_string = date_time.strftime('%Y-%m-%d %H:%M:%S')
        plain_text = remove_ansi_code_from_text(record.msg)
        
        return '{} - {} - {}'.format(date_string, record.levelname, plain_text)
