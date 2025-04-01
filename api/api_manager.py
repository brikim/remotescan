from logging import Logger
from common import utils

from api.plex import PlexAPI
from api.emby import EmbyAPI
from api.jellyfin import JellyfinAPI


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
        self.plex_api: PlexAPI = None
        self.emby_api_list: list[EmbyAPI] = []
        self.jellyfin_api: JellyfinAPI = None
        self.logger = logger

        # Plex API setup
        if "plex_url" in config and "plex_api_key" in config:
            self.plex_api = PlexAPI(
                config["plex_url"], config["plex_api_key"], self.logger
            )
            if self.plex_api.get_valid():
                self.logger.info(
                    f"Connected to {utils.get_formatted_plex()}({self.plex_api.get_name()}) successfully"
                )
            else:
                tag_plex_url = utils.get_tag("url", config["plex_url"])
                tag_plex_api = utils.get_tag("api_key", config["plex_api_key"])
                self.logger.warning(
                    f"{utils.get_formatted_plex()} server not available. Is this correct {tag_plex_url} {tag_plex_api}"
                )
        elif "plex_url" in config or "plex_api_key" in config:
            self.logger.warning(
                f"{utils.get_formatted_plex()} configuration error must define both plex_url and plex_api_key"
            )

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
                            f"{utils.get_formatted_emby()} {server["server_name"]} server not available. Is this correct {tag_emby_url} {tag_emby_api}"
                        )
                else:
                    self.logger.warning(
                        f"{utils.get_formatted_emby()} configuration error must define name, url and api_key for a server"
                    )

        # Jellyfin API setup
        if "jellyfin_url" in config and "jellyfin_api_key" in config:
            self.jellyfin_api = JellyfinAPI(
                config["jellyfin_url"], config["jellyfin_api_key"], self.logger
            )
            if self.jellyfin_api.get_valid():
                self.logger.info(
                    f"Connected to {utils.get_formatted_jellyfin()}({self.jellyfin_api.get_name()}) successfully"
                )
            else:
                tag_jellyfin_url = utils.get_tag("url", config["jellyfin_url"])
                tag_jellyfin_api = utils.get_tag(
                    "api_key", config["jellyfin_api_key"])
                self.logger.warning(
                    f"{utils.get_formatted_jellyfin()} server not available. Is this correct {tag_jellyfin_url} {tag_jellyfin_api}"
                )
        elif "jellyfin_url" in config or "jellyfin_api_key" in config:
            self.logger.warning(
                f"{utils.get_formatted_jellyfin()} configuration error must define both jellyfin_url and jellyfin_api_key"
            )

    def get_plex_api(self) -> PlexAPI:
        """
        Returns the PlexAPI instance.

        Returns:
            PlexAPI: The PlexAPI instance, or None if not configured.
        """
        return self.plex_api

    def get_emby_api(self, name: str) -> EmbyAPI:
        """
        Returns the EmbyAPI instance.

        Returns:
            EmbyAPI: The EmbyAPI instance, or None if not configured.
        """
        for emby_api in self.emby_api_list:
            if emby_api.get_server_name() == name:
                return emby_api
        return None

    def get_jellyfin_api(self) -> JellyfinAPI:
        """
        Returns the JellyfinAPI instance.
        Returns:
            JellyfinAPI: The JellyfinAPI instance, or None if not configured.
        """
        return self.jellyfin_api
