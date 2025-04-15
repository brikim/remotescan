""" Jellyfin API Module """

import requests
from requests.exceptions import RequestException

from api.api_base import ApiBase
from common import utils
from common.log_manager import LogManager


class JellyfinAPI(ApiBase):
    """
    Provides an interface for interacting with the Jellyfin Media Server API.

    This class extends ApiBase and provides methods for checking server
    validity, retrieving server name, checking library existence, and
    triggering library scans.
    """

    def __init__(
        self,
        server_name: str,
        url: str,
        api_key: str,
        log_manager: LogManager
    ):
        """
        Initializes the JellyfinAPI with the server URL, API key, and log_manager.

        Args:
            url (str): The base URL of the Jellyfin Media Server.
            api_key (str): The API key for authenticating with the Jellyfin server.
            log_manager (LogManager): The log_manager instance for logging messages.
        """
        super().__init__(
            server_name,
            url,
            api_key,
            utils.get_jellyfin_ansi_code(),
            self.__module__,
            log_manager
        )

    def __get_api_url(self) -> str:
        """
        Constructs the base API URL for Jellyfin.

        Returns:
            str: The base API URL.
        """
        return self.url

    def __get_default_payload(self) -> dict:
        """
        Returns the default payload for API requests.

        Returns:
            dict: The default payload containing the API key.
        """
        return {"api_key": self.api_key}

    def get_valid(self) -> bool:
        """
        Checks if the connection to the Jellyfin Media Server is valid.

        Returns:
            bool: True if the connection is valid, False otherwise.
        """
        try:
            r = requests.get(
                f"{self.__get_api_url()}/System/Configuration",
                params=self.__get_default_payload(),
                timeout=5
            )

            if r.status_code < 300:
                return True
        except RequestException:
            pass
        return False

    def get_server_reported_name(self) -> str:
        """
        Retrieves the friendly name of the Jellyfin Media Server.

        Returns:
            str: The friendly name of the Jellyfin server.
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
                self.log_manager.log_error(
                    f"{self.log_header} get_name {utils.get_tag('error', 'ServerName not found')}"
                )
        except RequestException as e:
            self.log_manager.log_error(
                f"{self.log_header} get_name {utils.get_tag("error", e)}"
            )
        return self.get_invalid_type()

    def set_library_scan(self, library_id: str):
        """
        Triggers a scan of the specified library on the Jellyfin server.

        Args:
            library_id (str): The ID of the library to scan.
        """
        try:
            headers = {"accept": "application/json"}

            # Set up the required payload
            payload: dict = self.__get_default_payload()
            payload["recursive"] = "true"
            payload["imageRefreshMode"] = "Default"
            payload["metadataRefreshMode"] = "Default"
            payload["replaceAllImages"] = "false"
            payload["replaceAllMetadata"] = "false"
            payload["regenerateTrickplay"] = "false"

            jellyfin_url = f"{self.__get_api_url()}/Items/{library_id}/Refresh"
            requests.post(
                jellyfin_url, headers=headers,
                params=payload, timeout=5
            )
        except RequestException as e:
            self.log_manager.log_error(
                f"{self.log_header} set_library_scan {utils.get_tag("error", e)}"
            )

    def get_library_id(self, name: str) -> str:
        """
        Retrieves the ID of a library with the given name on the Jellyfin server.

        Args:
            name (str): The name of the library to find.

        Returns:
            str: The ID of the library if found, otherwise the invalid item ID.
        """
        try:
            r = requests.get(
                f"{self.__get_api_url()}/Library/MediaFolders",
                params=self.__get_default_payload(),
                timeout=5
            )

            response = r.json()

            for library in response["Items"]:
                if "Name" in library and library["Name"] == name and "Id" in library:
                    return library["Id"]
        except RequestException as e:
            self.log_manager.log_error(
                f"{self.log_header} get_library_id {utils.get_tag("error", e)}"
            )

        return self.get_invalid_type()
