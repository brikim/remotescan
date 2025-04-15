""" API Base Module """

from typing import Any

from common import utils
from common.log_manager import LogManager

class ApiBase:
    """
    Base class for API interactions with media servers.
    Provides common functionality for API classes like setting up the URL,
    API key, log_manager, and log header.
    """

    def __init__(
        self,
        server_name: str,
        url: str,
        api_key: str,
        ansi_code: str,
        module: str,
        log_manager: LogManager
    ):
        """
        Initializes the ApiBase with the server URL, API key, ANSI code, module name, and log_manager.

        Args:
            server_name (str): The name to identify this server
            url (str): The base URL of the media server.
            api_key (str): The API key for authenticating with the server.
            ansi_code (str): The ANSI escape code for log header coloring.
            module (str): The name of the module using this class.
            log_manager (LogManager): The log_manager instance for logging messages.
        """
        self.server_name = server_name
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.log_manager = log_manager
        self.invalid_item_id = "0"
        self.log_header = utils.get_log_header(ansi_code, module)
        self.invalid_type = None

    def get_valid(self) -> bool:
        """
        Checks if the connection to the media server is valid. (To be implemented by subclasses)
        """
        return False

    def get_server_name(self) -> str:
        """
        Returns the server name pass in the constructor.

        Returns:
            str: The configured name of the server
        """
        return self.server_name

    def get_name(self) -> str:
        """
        Retrieves the friendly name of the media server. (To be implemented by subclasses)
        """
        return ""

    def get_invalid_type(self) -> Any:
        """
        Get the invalid type for the media servers

        Returns:
            Any: Invalid Type
        """
        return self.invalid_type
