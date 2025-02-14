from logging import Logger
from common.utils import get_log_header

class ApiBase:
    def __init__(self, url: str, api_key: str, ansi_code: str, module: str, logger: Logger):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.logger = logger
        self.invalid_item_id = '0'
        self.log_header = get_log_header(ansi_code, module)
        
    def get_valid(self) -> bool:
        return False
    
    def get_name(self) -> str:
        return ''
