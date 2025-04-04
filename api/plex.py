from logging import Logger
from plexapi.server import PlexServer
from common import utils

from api.api_base import ApiBase


class PlexAPI(ApiBase):
    """
    Provides an interface for interacting with the Plex Media Server API.

    This class extends ApiBase and provides methods for checking server
    validity, retrieving server name, checking library existence, and
    triggering library scans.
    """

    def __init__(
        self,
        url: str,
        api_key: str,
        logger: Logger
    ):
        """
        Initializes the PlexAPI with the server URL, API key, and logger.

        Args:
            url (str): The base URL of the Plex Media Server.
            api_key (str): The API key for authenticating with the Plex server.
            logger (Logger): The logger instance for logging messages.
        """
        super().__init__(
            url,
            api_key,
            utils.get_plex_ansi_code(),
            self.__module__,
            logger
        )
        self.plex_server = PlexServer(url.rstrip("/"), api_key)

    def get_valid(self) -> bool:
        """
        Checks if the connection to the Plex Media Server is valid.

        Returns:
            bool: True if the connection is valid, False otherwise.
        """
        try:
            self.plex_server.library.sections()
            return True
        except Exception:
            pass
        return False

    def get_name(self) -> str:
        """
        Retrieves the friendly name of the Plex Media Server.

        Returns:
            str: The friendly name of the Plex server.
        """
        return self.plex_server.friendlyName

    def get_library_exists(self, library_name: str) -> bool:
        """
        Checks if a library with the given name exists on the Plex server.

        Args:
            library_name (str): The name of the library to check.

        Returns:
            bool: True if the library exists, False otherwise.
        """
        try:
            self.plex_server.library.section(library_name)
            return True
        except Exception:
            pass
        return False

    def set_library_scan(self, library_name: str):
        """
        Triggers a scan of the specified library on the Plex server.

        Args:
            library_name (str): The name of the library to scan.
        """
        try:
            library = self.plex_server.library.section(library_name)
            library.update()
        except Exception as e:
            tag_library = utils.get_tag("library", library_name)
            tag_error = utils.get_tag("error", e)
            self.logger.error(
                f"{self.log_header} set_library_scan {tag_library} {tag_error}"
            )
