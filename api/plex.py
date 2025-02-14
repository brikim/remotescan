from logging import Logger
from typing import Any
from plexapi.server import PlexServer
from common import utils

from api.api_base import ApiBase

class PlexAPI(ApiBase):
    def __init__(self, url: str, api_key: str, logger: Logger):
        super().__init__(url, api_key, utils.get_plex_ansi_code(), self.__module__, logger)
        self.plex_server = PlexServer(url.rstrip('/'), api_key)
        self.item_invalid_type = None
        
    def get_valid(self) -> bool:
        try:
            self.plex_server.library.sections()
            return True
        except Exception as e:
            pass
        return False
    
    def get_name(self) -> str:
        return self.plex_server.friendlyName
        
    def get_invalid_type(self) -> Any:
        return self.item_invalid_type
    
    def get_library(self, library_name: str) -> Any:
        try:
            return self.plex_server.library.section(library_name)
        except Exception as e:
            self.logger.error("{} get_library {} {}".format(self.log_header, utils.get_tag('library', library_name), utils.get_tag('error', e)))
        return self.get_invalid_type()
    
    def set_library_scan(self, library_name: str):
        try:
            library = self.plex_server.library.section(library_name)
            library.update()
        except Exception as e:
            self.logger.error("{} set_library_scan {} {}".format(self.log_header, utils.get_tag('library', library_name), utils.get_tag('error', e)))
