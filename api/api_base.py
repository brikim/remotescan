from logging import Logger
from common.utils import get_log_header


class ApiBase:
    """
    Base class for API interactions with media servers.
    Provides common functionality for API classes like setting up the URL,
    API key, logger, and log header.
    """

    def __init__(
        self,
        url: str,
        api_key: str,
        ansi_code: str,
        module: str,
        logger: Logger
    ):
        """
        Initializes the ApiBase with the server URL, API key, ANSI code, module name, and logger.

        Args:
            url (str): The base URL of the media server.
            api_key (str): The API key for authenticating with the server.
            ansi_code (str): The ANSI escape code for log header coloring.
            module (str): The name of the module using this class.
            logger (Logger): The logger instance for logging messages.
        """

        self.url = url.rstrip("/")
        self.api_key = api_key
        self.logger = logger
        self.invalid_item_id = "0"
        self.log_header = get_log_header(ansi_code, module)

    def get_valid(self) -> bool:
        """
        Checks if the connection to the media server is valid. (To be implemented by subclasses)
        """
        return False

    def get_name(self) -> str:
        """
        Retrieves the friendly name of the media server. (To be implemented by subclasses)
        """
        return ""
