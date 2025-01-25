import requests
import json
from common.utils import get_jellyfin_ansi_code, get_log_header, get_tag

class JellyfinAPI:
    def __init__(self, url, api_key, logger):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.logger = logger
        self.invalid_item_id = '0'
        self.valid = False
        self.log_header = get_log_header(get_jellyfin_ansi_code(), self.__module__)
        
        try:
            payload = {'api_key': self.api_key}
            r = requests.get(self.get_api_url() + '/System/Configuration', params=payload)
            if r.status_code < 300:
                self.valid = True
        except Exception as e:
            self.valid = False
        
    def get_valid(self):
        return self.valid
    
    def get_invalid_item_id(self):
        return self.invalid_item_id
    
    def get_api_url(self):
        return self.url
    
    def set_library_scan(self, library_id):
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
            jellyfinUrl = self.get_api_url() + '/Items/' + library_id + '/Refresh'
            requests.post(jellyfinUrl, headers=headers, params=payload)
        except Exception as e:
            self.logger.error("{} Set Jellyfin library scan ERROR:{}".format(self.log_header, e))
    
    def get_library_from_name(self, name):
        try:
            payload = {'api_key': self.api_key}
            r = requests.get(self.get_api_url() + '/Library/MediaFolders', params=payload)
            response = r.json()

            for library in response['Items']:
                if library['Name'] == name:
                    return library
        except Exception as e:
            self.logger.error("{} get_library_from_name {}".format(self.log_header, get_tag('error', e)))
        
        self.logger.warning("{} get_library_from_name no library found with {}".format(self.log_header, get_tag('name', name)))
        return self.invalid_item_id
