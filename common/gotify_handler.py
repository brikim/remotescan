
import requests
import logging

class GotifyHandler(logging.Handler):
    def __init__(
        self,
        url: str,
        app_token: str,
        title: str,
        priority: int
    ):
        self.url = url.rstrip("/")
        self.app_token = app_token
        self.title = title
        self.priority = priority
        logging.Handler.__init__(self=self)

    def emit(self, record: logging.LogRecord):
        try:
            formatted_message = self.formatter.format(record)
            requests.post(self.url + "/message?token=" + self.app_token, json={
                        "message": formatted_message,
                        "priority": self.priority,
                        "title": self.title + " - " + record.levelname})
        except:
            self.handleError(record)
