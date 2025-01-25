import requests
import json
from common.utils import get_tag, get_log_header, get_emby_ansi_code

class EmbyAPI:
    def __init__(self, url, api_key, logger):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.logger = logger
        self.invalid_item_id = '0'
        self.valid = False
        self.log_header = get_log_header(get_emby_ansi_code(), self.__module__)
        
        try:
            payload = {'api_key': self.api_key}
            r = requests.get(self.get_api_url() + '/System/Configuration', params=payload)
            if r.status_code < 300:
                self.valid = True
            else:
                self.logger.warning('{} could not connect to service {}'.format(self.log_header, get_tag('status_code', r.status_code)))
        except Exception as e:
            self.logger.error('{} connection {}'.format(self.log_header, get_tag('error', e)))
            self.valid = False
        
    def get_valid(self):
        return self.valid
    
    def get_invalid_item_id(self):
        return self.invalid_item_id
    
    def get_api_url(self):
        return self.url + '/emby'
    
    def set_library_scan(self, library_id):
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
    
    def get_library_from_name(self, name):
        try:
            payload = {'api_key': self.api_key}
            r = requests.get(self.get_api_url() + '/Library/SelectableMediaFolders', params=payload)
            response = r.json()

            for library in response:
                if library['Name'] == name:
                    return library
        except Exception as e:
            self.logger.error("{} get_library_from_name {}".format(self.log_header, get_tag('error', e)))
        
        self.logger.warning("{} get_library_from_name no library found with {}".format(self.log_header, get_tag('name', name)))
        return self.invalid_item_id
