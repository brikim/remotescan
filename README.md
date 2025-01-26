# Autoscan

Uses iNotify to process file changes and notify Plex, Emby and/or Jellyfin.
This replaces the default Plex, Emby and Jellyfin scan my library automatically function.
This should be used if your media is stored on a different PC (a NAS) than your media server.

Autoscan uses python to monitor defined folders, add new folders to monitor and remove deleted folders from monitor. Once a change is detected monitors will wait for a defined time before requesting the media server to scan for changes. This is done so that multiple new files being added do not flood the media server with scan requests.

## Installing Autoscan
Autoscan offers a pre-compiled docker image (https://hub.docker.com/repository/docker/brikim/autoscan/general)

### Recommended usage
User docker compose to install auto scan

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
      - /docker/autoscan/config:/config
      - /docker/autoscan/logs:/logs
      - /pathToMedia:/media
    restart: unless-stopped
```

### Environment Variables
| Env | Function |
| :------- | :------------------------ |
| TZ       | specify a timezone to use |

## Logs

You can also export the logs by mounting a volume on `/logs`:
```
volumes:
    /logPath:/logs
```
