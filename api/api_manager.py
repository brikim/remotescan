from logging import Logger
from common import utils

from api.plex import PlexAPI
from api.emby import EmbyAPI
from api.jellyfin import JellyfinAPI

class ApiManager:
    def __init__(
        self, 
        config: dict,
        logger: Logger
    ):
        # Available API's
        self.plex_api: PlexAPI = None
        self.emby_api: EmbyAPI = None
        self.jellyfin_api: JellyfinAPI = None
    
        # Create all the api servers
        if "plex_url" in config and "plex_api_key" in config:
            self.plex_api = PlexAPI(
                config["plex_url"],
                config["plex_api_key"],
                logger
            )
            if self.plex_api.get_valid():
                logger.info(
                    f"Connected to {utils.get_formatted_plex()}:{self.plex_api.get_name()} successfully"
                )
            else:
                tag_plex_url = utils.get_tag("url", config["plex_url"])
                tag_plex_api = utils.get_tag("api_key", config["plex_api_key"])
                logger.warning(
                    f"{utils.get_formatted_plex()} server not available. Is this correct {tag_plex_url} {tag_plex_api}"
                )
        elif "plex_url" in config or "plex_api_key" in config:
            logger.warning(
                f"{utils.get_formatted_plex()} configuration error must define both plex_url and plex_api_key"
            )
            
        
        if "emby_url" in config and "emby_api_key" in config:
            self.emby_api = EmbyAPI(
                config["emby_url"],
                config["emby_api_key"],
                logger
            )
            if self.emby_api.get_valid():
                logger.info(
                    f"Connected to {utils.get_formatted_emby()}:{self.emby_api.get_name()} successfully"
                )
            else:
                tag_emby_url = utils.get_tag("url", config["emby_url"])
                tag_emby_api = utils.get_tag("api_key", config["emby_api_key"])
                logger.warning(
                    f"{utils.get_formatted_emby()} server not available. Is this correct {tag_emby_url} {tag_emby_api}"
                )
        elif "emby_url" in config or "emby_api_key" in config:
            logger.warning(
                f"{utils.get_formatted_emby()} configuration error must define both emby_url and emby_api_key"
            )
                
        if "jellyfin_url" in config and "jellyfin_api_key" in config:
            self.jellyfin_api = JellyfinAPI(
                config["jellyfin_url"],
                config["jellyfin_api_key"],
                logger
            )
            if self.jellyfin_api.get_valid():
                logger.info(
                    f"Connected to {utils.get_formatted_jellyfin()}:{self.jellyfin_api.get_name()} successfully"
                )
            else:
                tag_jellyfin_url = utils.get_tag("url", config["jellyfin_url"])
                tag_jellyfin_api = utils.get_tag("api_key", config["jellyfin_api_key"])
                logger.warning(
                    f"{utils.get_formatted_jellyfin()} server not available. Is this correct {tag_jellyfin_url} {tag_jellyfin_api}"
                )
        elif "jellyfin_url" in config or "jellyfin_api_key" in config:
            logger.warning(
                f"{utils.get_formatted_jellyfin()} configuration error must define both jellyfin_url and jellyfin_api_key"
            )
        
    def get_plex_api(self) -> PlexAPI:
        return self.plex_api
    
    def get_emby_api(self) -> EmbyAPI:
        return self.emby_api
    
    def get_jellyfin_api(self) -> JellyfinAPI:
        return self.jellyfin_api
