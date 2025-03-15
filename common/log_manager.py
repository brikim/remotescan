import logging
import colorlog

from logging import Logger
from logging.handlers import RotatingFileHandler

from common.gotify_handler import GotifyHandler
from common.plain_text_formatter import PlainTextFormatter
from common.gotify_plain_text_formatter import GotifyPlainTextFormatter
from common import utils

from typing import Optional


class LogManager:
    def __init__(
        self,
        log_name: str,
    ):
        self.logger = logging.getLogger(log_name)
        
        date_format = "%Y-%m-%d %H:%M:%S"
        log_colors = {
            "DEBUG": "cyan",
            "INFO": "light_green",
            "WARNING": "light_yellow",
            "ERROR": "light_red",
            "CRITICAL": "bold_red"}

        # Set up the logger
        self.logger.setLevel(logging.INFO)
        formatter = PlainTextFormatter()

        # Create a file handler to write logs to a file
        rotating_handler = RotatingFileHandler(
            "/logs/remotescan.log",
            maxBytes=100000,
            backupCount=5
        )
        rotating_handler.setLevel(logging.INFO)
        rotating_handler.setFormatter(formatter)

        # Create a stream handler to print logs to the console
        console_info_handler = colorlog.StreamHandler()
        console_info_handler.setLevel(logging.INFO)
        console_info_handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(white)s%(asctime)s %(light_white)s- %(log_color)s%(levelname)s %(light_white)s- %(message)s",
                date_format,
                log_colors=log_colors
            )
        )
        
        self.logger.addHandler(rotating_handler)
        self.logger.addHandler(console_info_handler)

    def configure_gotify(self, config: dict):
        # Create a Gotify log handler if set to log warnings 
        # and errors to the Gotify instance
        if (
            "gotify_logging" in config
            and "enabled" in config["gotify_logging"]
            and config["gotify_logging"]["enabled"] == "True"
        ):
            try:
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
            except Exception as e:
                self.logger.warning(
                    f"Configuration error for gotify logging {utils.get_tag("error", e)}"
                )
            
    def get_logger(self) -> Logger:
        return self.logger
    