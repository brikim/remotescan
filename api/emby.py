from logging import Logger
import requests
from common import utils

from api.api_base import ApiBase


class EmbyAPI(ApiBase):
    """
    Provides an interface for interacting with the Emby Media Server API.

    This class extends ApiBase and provides methods for checking server
    validity, retrieving server name, checking library existence, and
    triggering library scans.
    """

    def __init__(
        self,
        server_name: str,
        url: str,
        api_key: str,
        logger: Logger
    ):
        """
        Initializes the EmbyAPI with the server URL, API key, and logger.

        Args:
            server_name (str): The name of this emby server
            url (str): The base URL of the Emby Media Server.
            api_key (str): The API key for authenticating with the Emby server.
            logger (Logger): The logger instance for logging messages.
        """
        super().__init__(
            url, api_key, utils.get_emby_ansi_code(), self.__module__, logger
        )
        self.server_name = server_name
        self.invalid_item_id = "0"

    def __get_api_url(self) -> str:
        """
        Constructs the base API URL for Emby.

        Returns:
            str: The base API URL.
        """
        return f"{self.url}/emby"

    def __get_default_payload(self) -> dict:
        """
        Returns the default payload for API requests.

        Returns:
            dict: The default payload containing the API key.
        """
        return {"api_key": self.api_key}

    def get_server_name(self) -> str:
        """
        Returns the server name pass in the constructor.

        Returns:
            str: The configured name of the server
        """
        return self.server_name

    def get_valid(self) -> bool:
        """
        Checks if the connection to the Emby Media Server is valid.

        Returns:
            bool: True if the connection is valid, False otherwise.
        """
        try:
            r = requests.get(
                f"{self.__get_api_url()}/System/Info",
                params=self.__get_default_payload(),
                timeout=5
            )

            if r.status_code < 300:
                return True
        except Exception:
            pass
        return False

    def get_invalid_item_id(self) -> str:
        """
        Returns the ID used to represent an invalid item.

        Returns:
            str: The invalid item ID.
        """
        return self.invalid_item_id

    def get_server_reported_name(self) -> str:
        """
        Retrieves the friendly name of the Emby Media Server.

        Returns:
            str: The friendly name of the Emby server.
        """
        try:
            r = requests.get(
                f"{self.__get_api_url()}/System/Info",
                params=self.__get_default_payload(),
                timeout=5
            )

            response = r.json()

            if "ServerName" in response:
                return response["ServerName"]
            else:
                self.logger.error(
                    f"{self.log_header} get_name {utils.get_tag('error', 'ServerName not found')}"
                )
        except Exception as e:
            self.logger.error(
                f"{self.log_header} get_name {utils.get_tag("error", e)}"
            )
        return self.invalid_item_id

    def set_library_scan(self, library_id: str):
        """
        Triggers a scan of the specified library on the Emby server.

        Args:
            library_id (str): The ID of the library to scan.
        """
        try:
            headers = {"accept": "application/json"}
            payload = {
                "api_key": self.api_key,
                "Recursive": "true",
                "ImageRefreshMode": "Default",
                "MetadataRefreshMode": "Default",
                "ReplaceAllImages": "false",
                "ReplaceAllMetadata": "false",
            }
            emby_url = f"{self.__get_api_url()}/Items/{library_id}/Refresh"
            requests.post(emby_url, headers=headers, params=payload, timeout=5)
        except Exception as e:
            self.logger.error(
                f"{self.log_header} set_library_scan {utils.get_tag("error", e)}"
            )

    def get_library_id(self, name: str) -> str:
        """
        Retrieves the ID of a library with the given name on the Emby server.

        Args:
            name (str): The name of the library to find.

        Returns:
            str: The ID of the library if found, otherwise the invalid item ID.
        """
        try:
            r = requests.get(
                f"{self.__get_api_url()}/Library/SelectableMediaFolders",
                params=self.__get_default_payload(),
                timeout=5
            )

            response = r.json()

            for library in response:
                if "Name" in library and library["Name"] == name:
                    return library["Id"]
        except Exception as e:
            self.logger.error(
                f"{self.log_header} get_library_id {utils.get_tag("error", e)}"
            )

        return self.invalid_item_id
