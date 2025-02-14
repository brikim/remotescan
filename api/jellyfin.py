import requests
from logging import Logger
from common import utils

from api.api_base import ApiBase

class JellyfinAPI(ApiBase):
    def __init__(self, url: str, api_key: str, logger: Logger):
        super().__init__(url, api_key, utils.get_jellyfin_ansi_code(), self.__module__, logger)
        self.invalid_item_id = '0'
    
    def __get_api_url(self) -> str:
        return self.url
    
    def get_valid(self) -> bool:
        try:
            payload = {'api_key': self.api_key}
            r = requests.get(self.__get_api_url() + '/System/Configuration', params=payload)
            if r.status_code < 300:
                return True
        except Exception as e:
            pass
        return False
    
    def get_name(self) -> str:
        try:
            payload = {'api_key': self.api_key}
            r = requests.get(self.__get_api_url() + '/System/Info', params=payload)
            response = r.json()
            return response['ServerName']
        except Exception as e:
            self.logger.error("{} get_name {}".format(self.log_header, utils.get_tag('error', e)))
        return self.invalid_item_id
            
    def get_invalid_item_id(self) -> str:
        return self.invalid_item_id
    
    def set_library_scan(self, library_id: str):
        try:
            headers = {'accept': 'application/json'}
            payload = {
                'api_key': self.api_key,
                'recursive': 'true',
                'imageRefreshMode': 'Default',
                'metadataRefreshMode': 'Default',
                'replaceAllImages': 'false',
                'replaceAllMetadata': 'false',
                'regenerateTrickplay': 'false'}
            jellyfinUrl = self.__get_api_url() + '/Items/' + library_id + '/Refresh'
            requests.post(jellyfinUrl, headers=headers, params=payload)
        except Exception as e:
            self.logger.error("{} Set Jellyfin library scan {}".format(self.log_header, utils.get_tag('error', e)))
    
    def get_library_id(self, name: str) -> str:
        try:
            payload = {'api_key': self.api_key}
            r = requests.get(self.__get_api_url() + '/Library/MediaFolders', params=payload)
            response = r.json()

            for library in response['Items']:
                if library['Name'] == name:
                    return library['Id']
        except Exception as e:
            self.logger.error("{} get_library_id {}".format(self.log_header, utils.get_tag('error', e)))
        
        return self.invalid_item_id
