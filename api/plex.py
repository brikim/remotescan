from logging import Logger
from typing import Any
from plexapi.server import PlexServer
from common import utils

from api.api_base import ApiBase

class PlexAPI(ApiBase):
    def __init__(
        self,
        url: str,
        api_key: str,
        logger: Logger
    ):
        super().__init__(
            url,
            api_key,
            utils.get_plex_ansi_code(),
            self.__module__,
            logger
        )
        self.plex_server = PlexServer(url.rstrip("/"), api_key)
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
            tag_library = utils.get_tag("library", library_name)
            tag_error = utils.get_tag("error", e)
            self.logger.error(
                f"{self.log_header} get_library {tag_library} {tag_error}"
            )
        return self.get_invalid_type()
    
    def set_library_scan(self, library_name: str):
        try:
            library = self.plex_server.library.section(library_name)
            library.update()
        except Exception as e:
            tag_library = utils.get_tag("library", library_name)
            tag_error = utils.get_tag("error", e)
            self.logger.error(
                f"{self.log_header} set_library_scan {tag_library} {tag_error}"
            )
