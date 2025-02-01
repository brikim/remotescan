import requests
from logging import Logger
from typing import Any
from common.utils import get_tag, get_log_header, get_emby_ansi_code

class EmbyAPI:
    def __init__(self, url: str, api_key: str, logger: Logger):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.logger = logger
        self.invalid_item_id = '0'
        self.log_header = get_log_header(get_emby_ansi_code(), self.__module__)
        
    def get_valid(self) -> bool:
        try:
            payload = {'api_key': self.api_key}
            r = requests.get(self.get_api_url() + '/System/Configuration', params=payload)
            if r.status_code < 300:
                return True
        except Exception as e:
            pass
        return False
    
    def get_invalid_item_id(self) -> str:
        return self.invalid_item_id
    
    def get_api_url(self) -> str:
        return self.url + '/emby'
    
    def set_library_scan(self, library_id: str):
        try:
            headers = {'accept': 'application/json'}
            payload = {
                'api_key': self.api_key,
                'Recursive': 'true',
                'ImageRefreshMode': 'Default',
                'MetadataRefreshMode': 'Default',
                'ReplaceAllImages': 'false',
                'ReplaceAllMetadata': 'false'}
            embyUrl = self.get_api_url() + '/Items/' + library_id + '/Refresh'
            requests.post(embyUrl, headers=headers, params=payload)
        except Exception as e:
            self.logger.error("{} set_library_scan {}".format(self.log_header, get_tag('error', e)))

    def get_library_id(self, name: str) -> str:
        try:
            payload = {'api_key': self.api_key}
            r = requests.get(self.get_api_url() + '/Library/SelectableMediaFolders', params=payload)
            response = r.json()

            for library in response:
                if library['Name'] == name:
                    return library['Id']
        except Exception as e:
            self.logger.error("{} get_library_id {}".format(self.log_header, get_tag('error', e)))
        
        return self.invalid_item_id