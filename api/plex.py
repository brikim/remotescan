""" Plex API Module """

from plexapi.server import PlexServer
from plexapi.exceptions import BadRequest, NotFound, Unauthorized

from api.api_base import ApiBase
from common import utils
from common.log_manager import LogManager

class PlexAPI(ApiBase):
    """
    Provides an interface for interacting with the Plex Media Server API.

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
        Initializes the PlexAPI with the server URL, API key, and log_manager.

        Args:
            url (str): The base URL of the Plex Media Server.
            api_key (str): The API key for authenticating with the Plex server.
            log_manager (LogManager): The log_manager instance for logging messages.
        """
        super().__init__(
            server_name,
            url,
            api_key,
            utils.get_plex_ansi_code(),
            self.__module__,
            log_manager
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
        except (BadRequest, NotFound, Unauthorized):
            pass
        return False

    def get_server_reported_name(self) -> str:
        """
        Retrieves the friendly name of the Plex Media Server.

        Returns:
            str: The friendly name of the Plex server.
        """
        try:
            return_name = self.plex_server.friendlyName
            return return_name
        except (BadRequest, NotFound, Unauthorized):
            pass
        return "Unknown Plex Server"

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
        except (BadRequest, NotFound, Unauthorized):
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
        except (BadRequest, NotFound, Unauthorized) as e:
            tag_library = utils.get_tag("library", library_name)
            tag_error = utils.get_tag("error", e)
            self.log_manager.log_error(
                f"{self.log_header} set_library_scan {tag_library} {tag_error}"
            )
