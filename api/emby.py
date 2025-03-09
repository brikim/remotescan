import requests
from logging import Logger
from common import utils

from api.api_base import ApiBase

class EmbyAPI(ApiBase):
    def __init__(
        self,
        url: str,
        api_key: str,
        logger: Logger
    ):
        super().__init__(
            url,
            api_key,
            utils.get_emby_ansi_code(),
            self.__module__,
            logger
        )
        self.invalid_item_id = "0"
    
    def __get_api_url(self) -> str:
        return self.url + "/emby"
    
    def __get_default_payload(self) -> dict:
        return {"api_key": self.api_key}
    
    def get_valid(self) -> bool:
        try:
            r = requests.get(
                self.__get_api_url() + "/System/Info",
                params=self.__get_default_payload()
            )
            if r.status_code < 300:
                return True
        except Exception as e:
            pass
        return False
    
    def get_invalid_item_id(self) -> str:
        return self.invalid_item_id
    
    def get_name(self) -> str:
        try:
            r = requests.get(
                self.__get_api_url() + "/System/Info",
                params=self.__get_default_payload()
            )
            response = r.json()
            return response["ServerName"]
        except Exception as e:
            self.logger.error(
                f"{self.log_header} get_name {utils.get_tag("error", e)}"
            )
        return self.invalid_item_id
    
    def set_library_scan(self, library_id: str):
        try:
            headers = {"accept": "application/json"}
            payload = {
                "api_key": self.api_key,
                "Recursive": "true",
                "ImageRefreshMode": "Default",
                "MetadataRefreshMode": "Default",
                "ReplaceAllImages": "false",
                "ReplaceAllMetadata": "false"}
            embyUrl = self.__get_api_url() + "/Items/" + library_id + "/Refresh"
            requests.post(embyUrl, headers=headers, params=payload)
        except Exception as e:
            self.logger.error(
                f"{self.log_header} set_library_scan {utils.get_tag("error", e)}"
            )

    def get_library_id(self, name: str) -> str:
        try:
            r = requests.get(
                self.__get_api_url() + "/Library/SelectableMediaFolders",
                params=self.__get_default_payload())
            response = r.json()

            for library in response:
                if library["Name"] == name:
                    return library["Id"]
        except Exception as e:
            self.logger.error(
                f"{self.log_header} get_library_id {utils.get_tag("error", e)}"
            )
        
        return self.invalid_item_id