""" API Manager Module """

from logging import Logger

from api.plex import PlexAPI
from api.emby import EmbyAPI
from api.jellyfin import JellyfinAPI
from common import utils


class ApiManager:
    """
    Manages the API connections to different media servers (Plex, Emby, Jellyfin).
    """

    def __init__(
        self,
        config: dict,
        logger: Logger
    ):
        """
        Initializes the ApiManager and establishes connections to configured media servers.
        """
        self.plex_api_list: list[PlexAPI] = []
        self.emby_api_list: list[EmbyAPI] = []
        self.jellyfin_api_list: list[JellyfinAPI] = []
        self.logger = logger

        # Plex API setup
        if "plex" in config:
            for server in config["plex"]:
                if "server_name" in server and "url" in server and "api_key" in server:
                    self.plex_api_list.append(
                        PlexAPI(
                            server["server_name"], server["url"], server["api_key"], self.logger
                        )
                    )
                    if self.plex_api_list[-1].get_valid():
                        self.logger.info(
                            f"Connected to {utils.get_formatted_plex()}({self.plex_api_list[-1].get_server_reported_name()}) successfully"
                        )
                    else:
                        tag_plex_url = utils.get_tag(
                            "url", server["url"]
                        )
                        tag_plex_api = utils.get_tag(
                            "api_key", server["api_key"]
                        )
                        self.logger.warning(
                            f"{utils.get_formatted_plex()}({server["server_name"]}) server not available. Is this correct {tag_plex_url} {tag_plex_api}"
                        )
                else:
                    self.logger.warning(
                        f"{utils.get_formatted_plex()} configuration error must define name, url and api_key for a server"
                    )

        # Emby API setup
        if "emby" in config:
            for server in config["emby"]:
                if "server_name" in server and "url" in server and "api_key" in server:
                    self.emby_api_list.append(
                        EmbyAPI(
                            server["server_name"], server["url"], server["api_key"], self.logger
                        )
                    )
                    if self.emby_api_list[-1].get_valid():
                        self.logger.info(
                            f"Connected to {utils.get_formatted_emby()}({self.emby_api_list[-1].get_server_reported_name()}) successfully"
                        )
                    else:
                        tag_emby_url = utils.get_tag(
                            "url", server["url"]
                        )
                        tag_emby_api = utils.get_tag(
                            "api_key", server["api_key"]
                        )
                        self.logger.warning(
                            f"{utils.get_formatted_emby()}({server["server_name"]}) server not available. Is this correct {tag_emby_url} {tag_emby_api}"
                        )
                else:
                    self.logger.warning(
                        f"{utils.get_formatted_emby()} configuration error must define name, url and api_key for a server"
                    )

        # Jellyfin API setup
        if "jellyfin" in config:
            for server in config["jellyfin"]:
                if "server_name" in server and "url" in server and "api_key" in server:
                    self.jellyfin_api_list.append(
                        JellyfinAPI(
                            server["server_name"], server["url"], server["api_key"], self.logger
                        )
                    )
                    if self.jellyfin_api_list[-1].get_valid():
                        self.logger.info(
                            f"Connected to {utils.get_formatted_jellyfin()}({self.jellyfin_api_list[-1].get_server_reported_name()}) successfully"
                        )
                    else:
                        tag_jellyfin_url = utils.get_tag(
                            "url", server["url"]
                        )
                        tag_jellyfin_api = utils.get_tag(
                            "api_key", server["api_key"]
                        )
                        self.logger.warning(
                            f"{utils.get_formatted_jellyfin()}({server["server_name"]}) server not available. Is this correct {tag_jellyfin_url} {tag_jellyfin_api}"
                        )
                else:
                    self.logger.warning(
                        f"{utils.get_formatted_jellyfin()} configuration error must define name, url and api_key for a server"
                    )

    def get_plex_api(self, name: str) -> PlexAPI:
        """
        Returns the PlexAPI instance with the given name.

        Returns:
            PlexAPI: The PlexAPI instance, or None if not configured.
        """
        for plex_api in self.plex_api_list:
            if plex_api.get_server_name() == name:
                return plex_api
        return None

    def get_emby_api(self, name: str) -> EmbyAPI:
        """
        Returns the EmbyAPI instance with the given name.

        Returns:
            EmbyAPI: The EmbyAPI instance, or None if not configured.
        """
        for emby_api in self.emby_api_list:
            if emby_api.get_server_name() == name:
                return emby_api
        return None

    def get_jellyfin_api(self, name: str) -> JellyfinAPI:
        """
        Returns the JellyfinAPI instance with the given name.
        Returns:
            JellyfinAPI: The JellyfinAPI instance, or None if not configured.
        """
        for jellyfin_api in self.jellyfin_api_list:
            if jellyfin_api.get_server_name() == name:
                return jellyfin_api
        return None
