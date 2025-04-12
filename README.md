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
    "plex": [
        {"server_name": "Server1", "url": "http://0.0.0.0:32400", "api_key": ""},
        {"server_name": "Server2", "url": "http://0.0.0.0:32401", "api_key": ""}
    ],

    "emby": [
        {"server_name": "Server1", "url": "http://0.0.0.0:8096", "api_key": ""},
        {"server_name": "Server2", "url": "http://0.0.0.0:8097", "api_key": ""}
    ],

    "jellyfin": [
        {"server_name": "Server1", "url": "http://0.0.0.0:8096", "api_key": ""},
        {"server_name": "Server2", "url": "http://0.0.0.0:8097", "api_key": ""}
    ],

    "gotify_logging": {
        "enabled": "False",
        "url": "",
        "app_token": "",
        "message_title": "Title of message",
        "priority": 6
    },
    
    "remote_scan": {
        "seconds_before_notify": 90,
        "seconds_between_notifies": 15,
        
        "scans": [
            {
                "name": "scanName", 
                "plex": [
                    {"server_name": "PlexServerNameFromAbove", "library": "Server1LibraryName"},
                    {"server_name": "PlexServerNameFromAbove", "library": "Server2LibraryName"}
                ],

                "emby": [
                   {"server_name": "Server1", "library": "Server1LibraryName"},
                   {"server_name": "Server2", "library": "Server2LibraryName"}
                ],

                "jellyfin": [
                    {"server_name": "JellyfinServerNameFromAbove", "library": "Server1LibraryName"},
                    {"server_name": "JellyfinServerNameFromAbove", "library": "Server2LibraryName"}
                ],

                "paths": [
                   { "container_path": "/media/Path1" },
                   { "container_path": "/media/Path2" }
                ]
            },
            {   
                "name": "scanName2", 
                "plex": [
                    {"server_name": "PlexServerNameFromAbove", "library": "Server1LibraryName2"},
                    {"server_name": "PlexServerNameFromAbove", "library": "Server2LibraryName2"}
                ],

                "emby": [
                   {"server_name": "Server1", "library": "Server1LibraryName2"},
                   {"server_name": "Server2", "library": "Server2LibraryName2"}
                ],

                "jellyfin": [
                    {"server_name": "JellyfinServerNameFromAbove", "library": "Server1LibraryName2"},
                    {"server_name": "JellyfinServerNameFromAbove", "library": "Server2LibraryName2"}
                ],
                
                "paths": [
                   { "container_path": "/media/Path1" },
                   { "container_path": "/media/Path2" }
                ]
            }
        ],

        "ignore_folders": [
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
| plex               | Plex configuration for one or multiple servers |
| emby               | Emby configuration for one or multiple servers |
| jellyfin           | Emby configuration for one or multiple servers |

##### Plex
| Plex Server | Function |
| :----------- | :------------------------ |
| server_name        | Name of this plex server to use as reference in this file |
| url                | Url to your plex server (Make sure you include the port if not reverse proxy) |
| api_key            | API Key to access this plex server |

##### Emby
| Emby Server | Function |
| :----------- | :------------------------ |
| server_name        | Name of this emby server to use as reference in this file |
| url                | Url to your emby server (Make sure you include the port if not reverse proxy) |
| api_key            | API Key to access this emby server |

##### Jellyfin
| Jellyfin Server | Function |
| :----------- | :------------------------ |
| server_name        | Name of this jellyfin server to use as reference in this file |
| url                | Url to your jellyfin server (Make sure you include the port if not reverse proxy) |
| api_key            | API Key to access this jellyfin server |

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
| plex             | Plex section to notify one to many plex servers of updates or changes. Not required. |
| emby             | Emby section to notify one to many emby servers of updates or changes. Not required. |
| jellyfin         | Jellyfin section to notify one to many jellyfin servers of updates or changes. Not required. |
| paths            | A list of physical paths defined by container_path to monitor for this scan. Paths should be based off of mounted volume /media or other as defined by user. Multiple paths needed if media server library consists of multiple paths |

##### Scan configuration Plex
| Plex Scan Configuration | Function |
| :----------- | :------------------------ |
| server_name        | Name of this plex server from the configured plex servers |
| library            | Plex library to notify of changes to this scan |

##### Scan configuration Emby
| Emby Scan Configuration | Function |
| :----------- | :------------------------ |
| server_name        | Name of this emby server from the configured emby servers |
| library            | Emby library to notify of changes to this scan |

##### Scan configuration Jellyfin
| Jellyfin Scan Configuration | Function |
| :----------- | :------------------------ |
| server_name        | Name of this jellyfin server from the configured jellyfin servers |
| library            | Jellyfin library to notify of changes to this scan |

#### Ignore Folders
Optional. List of folders to ignore.
```
**WARNING**
Be careful with the name! If it is too generic the folder may get ignored for the monitors.
```
An example usage would be for synology NAS ignore @eaDir folders
| Ignore folders | Function |
| :--------------- | :------------------------ |
| ignore_folder    | Ignore updates for paths containing the folder |

#### Valid File Extensions
Optional. List of valid file extensions that must be in the folder to notify media servers to re-scan
| Valid File Extension | Function |
| :--------------- | :------------------------ |
| valid_file_extensions    | A comma separated list of extensions. If defined the monitor has to detect a change to this type of file before notifying media servers |