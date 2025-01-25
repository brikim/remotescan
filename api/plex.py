import requests
import json
from plexapi.server import PlexServer
from common.utils import get_plex_ansi_code, get_log_header, get_tag

class PlexAPI:
    def __init__(self, url, api_key, logger):
        self.plex_server = PlexServer(url.rstrip('/'), api_key)
        self.logger = logger
        self.item_invalid_type = None
        self.valid = False
        self.log_header = get_log_header(get_plex_ansi_code(), self.__module__)
        
        try:
            self.plex_server.library.sections()
            self.valid = True
        except Exception as e:
            self.logger.warning('{} could not connect to service'.format(self.log_header))
            self.valid = False
        
    def get_valid(self):
        return self.valid
    
    def get_invalid_type(self):
        return self.item_invalid_type
    
    def get_library(self, library_name):
        try:
            return self.plex_server.library.section(library_name)
        except Exception as e:
            pass
        return self.get_invalid_type()
    
    def set_library_scan(self, library_name):
        try:
            library = self.plex_server.library.section(library_name)
            library.update()
        except Exception as e:
            self.logger.error("{} set_library_scan {} {}".format(self.log_header, get_tag('library', library_name), get_tag('error', e)))
