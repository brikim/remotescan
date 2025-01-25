# autoscan
Uses iNotify to process file changes and notify Plex, Emby and/or Jellyfin

## First run 

```
run docker compose on example compose.yml
```

## Logs

You can also export the logs by mounting a volume on `/logs`:
```
volumes:
    /logPath:/logs
```
