
import logging
import requests


class GotifyHandler(logging.Handler):
    """ 
    Gotify logging handler for Python.

    This handler sends log messages to a Gotify server.
    """

    def __init__(
        self,
        url: str,
        app_token: str,
        title: str,
        priority: int
    ):
        """
        Initializes the GotifyHandler with the Gotify server details.

        Args:
            url (str): The base URL of the Gotify server.
            app_token (str): The application token for authenticating with Gotify.
            title (str): The base title for Gotify messages.
            priority (int): The priority level for Gotify messages.
        """
        self.url = url.rstrip("/")
        self.app_token = app_token
        self.title = title
        self.priority = priority
        logging.Handler.__init__(self=self)

    def emit(self, record: logging.LogRecord):
        """
        Emits a log record to the Gotify server.

        Args:
            record (logging.LogRecord): The log record to emit.
        """
        try:
            formatted_message = self.formatter.format(record)
            requests.post(
                f"{self.url}/message?token={self.app_token}",
                json={
                    "message": formatted_message,
                    "priority": self.priority,
                    "title": f"{self.title} - {record.levelname}"
                },
                timeout=5,
            )
        except Exception:
            self.handleError(record)
