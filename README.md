# Remotescan
Remotescan replaces the default Plex, Emby and Jellyfin scan my library automatically function. The Remotescan docker container should be run on the PC where your media is stored. It will then be configured to notify your media server of any changes(New, Modify and Delete)
> [!NOTE]
> 📝 The scan for new media function of your media server will not work over network shares(NFS or SAMBA).

Uses iNotify to process file changes and notify Plex, Emby and/or Jellyfin.

Remotescan uses python to monitor defined folders, add new folders to monitor and remove deleted folders from monitor. Once a change is detected monitors will wait for a defined time before requesting the media server to scan for changes. This is done so that multiple new files being added do not flood the media server with scan requests.

## Installing Remotescan
Remotescan offers a pre-compiled [docker image](https://hub.docker.com/repository/docker/brikim/remotescan/general)

### Usage
Use docker compose to run Remotescan

### compose.yml
```yaml
---
services:
  remotescan:
    container_name: remotescan
    image: brikim/remotescan:latest
    security_opt:
      - no-new-privileges:true
    environment:
      - TZ=Etc/UTC
    volumes:
      - /docker/remotescan/config:/config:ro
      - /docker/remotescan/logs:/logs
      - /pathToMedia:/media
    restart: unless-stopped
```
> [!NOTE]
> 📝 /media folder can not be read only for the docker container to shut down nicely

### Environment Variables
| Env | Function |
| :------- | :------------------------ |
| TZ       | specify a timezone to use |

### Volume Mappings
| Volume | Function |
| :------- | :------------------------ |
| /config  | Path to a folder containing config.yml used to setup Remotescan |
| /logs    | Path to a folder to store Remotescan log files |
| /media   | Path to your media files. Used to scan directories for changes |

### Configuration File
A configuration file is required to use Remotescan. Create a config.yml file in the volume mapped to /config

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
        "enabled": "False",
        "url": "",
        "app_token": "",
        "message_title": "Title of message",
        "priority": 6
    },
    
    "auto_scan": {
        "seconds_before_notify": 90,
        "seconds_between_notifies": 15,
        
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

#### Remotescan configuration

| Remotescan | Function |
| :--------------- | :------------------------ |
| seconds_before_notify    | How long to wait after changes detected before sending scan request to media servers. Not required. Default: 90 |
| seconds_between_notifies | How many seconds to wait between media server scan requests. Not required. Default: 15 |

1 to many scans can be defined as a list
| Scans | Function |
| :--------------- | :------------------------ |
| name             | Unique name defined for this scan |
| plex_library     | Plex library to notify of updates on monitor changes. Not required. |
| emby_library     | Emby library to notify of updates on monitor changes. Not required. |
| jellyfin_library | Jellyfin library to notify of updates on monitor changes. Not required. |
| paths            | A list of physical paths defined by container_path to monitor for this scan. Paths should be based off of mounted volume /media or other as defined by user. Multiple paths needed if media server library consists of multiple paths |

Optional. List of folders to ignore.
```
**WARNING**
Be careful with the name! If it is too generic the folder may get ignored for the monitors.
```
An example usage would be for synology NAS ignore @eaDir folders
| Ignore folders | Function |
| :--------------- | :------------------------ |
| ignore_folder    | Ignore updates for paths containing the folder |

Optional. List of valid file extensions that must be in the folder to notify media servers to re-scan
| Valid File Extension | Function |
| :--------------- | :------------------------ |
| valid_file_extensions    | A comma separated list of extensions. If defined the monitor has to detect a change to this type of file before notifying media servers |
