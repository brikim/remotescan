# Autoscan

Uses iNotify to process file changes and notify Plex, Emby and/or Jellyfin.
This replaces the default Plex, Emby and Jellyfin scan my library automatically function.
This should be used if your media is stored on a different PC (a NAS) than your media server.

Autoscan uses python to monitor defined folders, add new folders to monitor and remove deleted folders from monitor. Once a change is detected monitors will wait for a defined time before requesting the media server to scan for changes. This is done so that multiple new files being added do not flood the media server with scan requests.

## Installing Autoscan
Autoscan offers a pre-compiled docker image (https://hub.docker.com/repository/docker/brikim/autoscan/general)

### Usage
User docker compose to install auto scan

### compose.yml
```yaml
---
services:
  autoscan:
    container_name: autoscan
    image: brikim/autoscan:latest
    security_opt:
      - no-new-privileges:true
    environment:
      - TZ=Etc/UTC
    volumes:
      - /docker/autoscan/config:/config:ro
      - /docker/autoscan/logs:/logs
      - /pathToMedia:/media:ro
    restart: unless-stopped
```

### Environment Variables
| Env | Function |
| :------- | :------------------------ |
| TZ       | specify a timezone to use |

### Volume Mappings
| Volume | Function |
| :------- | :------------------------ |
| /config  | Path to a folder containing config.yml used to setup Autoscan |
| /logs    | Path to a folder to store Autoscan log files |
| /media   | Path to your media files. Used to scan directories for changes |

### Configuration File
A configuration file is required to use Autoscan. Create a config.yml file in the volume mapped to /config

#### config.yml
```yaml
{
    "plex_url": "http://0.0.0.0:32400",
    "plex_api_key": "",

    "emby_url": "http://0.0.0.0:8096",
    "emby_api_key": "",

    "jellyfin_url": "http://0.0.0.0:8096",
    "jellyfin_api_key": "",

    "gotify_logging": {
        "enabled": "True",
        "url": "",
        "app_token": "",
        "message_title": "Title of message",
        "priority": 6
    },
    
    "auto_scan": {
        "seconds_monitor_rate": 1,
        "seconds_before_notify": 90,
        "seconds_between_notifies": 15,
        "seconds_before_inotify_modify": 1,
        
        "scans": [
            {"name": "scanName", 
             "plex_library": "plexLibraryName", 
             "emby_library": "EmbyLibraryName", 
             "jellyfin_library": "JellyfinLibraryName",
             "paths": [
                { "container_path": "/media/Path1" },
                { "container_path": "/media/Path2" }
             ]
            },
            {"name": "scanName2", 
             "plex_library": "plexLibraryName", 
             "emby_library": "EmbyLibraryName", 
             "jellyfin_library": "JellyfinLibraryName",
             "paths": [
                { "container_path": "/media/Path3" }
             ]
            }
        ],

        "ignore_folder_with_name": [
            {"ignore_folder": "someFolderToIgnore1"},
            {"ignore_folder": "someFolderToIgnore2"}
        ],

        "valid_file_extensions": "mkv,mp4,png"
    }
}
```

#### Option Descriptions
You only have to define the variables for servers in your system. For plex only define plex_url and plex_api_key in your file. The emby and jellyfin variables are not required.
| Media Server | Function |
| :----------- | :------------------------ |
| plex_url           | Url to your plex server (Make sure you include the port if not reverse proxy) |
| plex_api_key       | API Key to access your plex server |
| emby_url           | Url to your emby server (Make sure you include the port if not reverse proxy) |
| emby_api_key       | API Key to access your emby server |
| jellyfin_url       | Url to your jellyfin server (Make sure you include the port if not reverse proxy) |
| jellyfin_api_key   | API Key to access your jellyfin server |

#### Gotify Logging
Not required unless wanting to send Warnings or Errors to Gotify
| Gotify | Function |
| :--------------- | :------------------------ |
| enabled          | Enable the function with 'True' |
| url              | Url including port to your gotify server |
| app_token        | Gotify app token to be used to send notifications |
| message_title    | Title to put in the title bar of the message |
| priority         | The priority of the message to send to gotify |

## Logs

You can also export the logs by mounting a volume on `/logs`:
```
volumes:
    /logPath:/logs
```
