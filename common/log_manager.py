
import logging
from logging import Logger
from logging.handlers import RotatingFileHandler

import colorlog

from common.gotify_handler import GotifyHandler
from common.gotify_plain_text_formatter import GotifyPlainTextFormatter
from common.plain_text_formatter import PlainTextFormatter


class LogManager:
    """
    Manages logging for the application, including file and console output,
    and optional Gotify notifications.
    """

    def __init__(
        self,
        log_name: str,
    ):
        """
        Initializes the LogManager with the specified log name.

        Args:
            log_name (str): The name of the logger.
        """
        self.logger = logging.getLogger(log_name)

        log_date_format = "%Y-%m-%d %H:%M:%S"
        log_colors = {
            "DEBUG": "cyan",
            "INFO": "light_green",
            "WARNING": "light_yellow",
            "ERROR": "light_red",
            "CRITICAL": "bold_red",
        }

        # Set up the logger
        self.logger.setLevel(logging.INFO)
        file_formatter = PlainTextFormatter()

        # Create a file handler to write logs to a file
        file_rotating_handler = RotatingFileHandler(
            "/logs/remotescan.log", maxBytes=100000, backupCount=5
        )
        file_rotating_handler.setLevel(logging.INFO)
        file_rotating_handler.setFormatter(file_formatter)

        # Create a stream handler to print logs to the console
        console_info_handler = colorlog.StreamHandler()
        console_info_handler.setLevel(logging.INFO)
        console_info_handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(white)s%(asctime)s %(light_white)s- %(log_color)s%(levelname)s %(light_white)s- %(message)s",
                log_date_format,
                log_colors=log_colors,
            )
        )

        self.logger.addHandler(file_rotating_handler)
        self.logger.addHandler(console_info_handler)

    def configure_gotify(self, config: dict) -> None:
        """Configures Gotify logging if enabled in the configuration."""
        # Create a Gotify log handler if set to log warnings
        # and errors to the Gotify instance
        if (
            "gotify_logging" in config
            and "enabled" in config["gotify_logging"]
            and config["gotify_logging"]["enabled"] == "True"
        ):
            if (
                "url" in config["gotify_logging"]
                and "app_token" in config["gotify_logging"]
                and "message_title" in config["gotify_logging"]
                and "priority" in config["gotify_logging"]
            ):
                gotify_formatter = GotifyPlainTextFormatter()
                gotify_handler = GotifyHandler(
                    config["gotify_logging"]["url"],
                    config["gotify_logging"]["app_token"],
                    config["gotify_logging"]["message_title"],
                    config["gotify_logging"]["priority"]
                )
                gotify_handler.setLevel(logging.WARNING)
                gotify_handler.setFormatter(gotify_formatter)

                # Add the gotify handler to the logger
                self.logger.addHandler(gotify_handler)
            else:
                self.logger.warning(
                    "Configuration gotify_logging enabled is True but missing an attribute url, app_token, message_title or priority"
                )

    def get_logger(self) -> Logger:
        """
        Returns the logger instance.

        Returns:
            Logger: The logger instance.
        """
        return self.logger
