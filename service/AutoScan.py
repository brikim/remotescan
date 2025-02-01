
import os
import time
from datetime import datetime
import threading
from threading import Thread
from dataclasses import dataclass, field
from logging import Logger
from apscheduler.schedulers.blocking import BlockingScheduler
from external.PyInotify.inotify import adapters, constants
from typing import Any, List
from api.plex import PlexAPI
from api.emby import EmbyAPI
from api.jellyfin import JellyfinAPI
from service.ServiceBase import ServiceBase
from common.utils import get_tag, get_formatted_emby, get_formatted_plex, get_formatted_jellyfin, build_target_string

@dataclass
class ScanConfigInfo:
    name: str
    plex_library: str
    emby_library: str
    jellyfin_library: str
    time: float
    paths: list[str] = field(default_factory=list)

@dataclass
class CheckPathData:
    path: str
    i: adapters.Inotify
    scan_mask: int
    time: float
    deleted: bool

class AutoScan(ServiceBase):
    def __init__(self, plex_api: PlexAPI, emby_api: EmbyAPI, jellyfin_api: JellyfinAPI, config: Any, logger: Logger, scheduler: BlockingScheduler):
        super().__init__(logger, scheduler)
        
        self.plex_api = plex_api
        self.emby_api = emby_api
        self.jellyfin_api = jellyfin_api
        
        self.ignore_folder_with_name: list[str] = []
        self.valid_file_extensions: list[str] = []
        
        self.seconds_monitor_rate: int = 1
        self.seconds_before_notify: int = 90
        self.seconds_between_notifies: int = 15
        self.seconds_before_inotify_modify: int = 1
        self.last_notify_time: float = 0.0
        
        self.scan_configs: list[ScanConfigInfo] = []
        
        self.monitors: list[ScanConfigInfo] = []
        self.monitor_lock = threading.Lock()
        self.monitor_thread: Thread = None
        
        self.watched_paths_lock = threading.Lock()
        self.watched_paths: list[str] = []
        
        self.threads: list[Thread] = []
        self.stop_threads = False
        
        self.check_new_paths_lock = threading.Lock()
        self.check_new_paths: list[CheckPathData] = []
        
        try:
            if 'seconds_monitor_rate' in config:
                self.seconds_monitor_rate = max(config['seconds_monitor_rate'], 1)
            if 'seconds_before_notify' in config:
                self.seconds_before_notify = max(config['seconds_before_notify'], 30)
            if 'seconds_between_notifies' in config:
                self.seconds_between_notifies = max(config['seconds_between_notifies'], 10)
            if 'seconds_before_inotify_modify' in config:
                self.seconds_before_inotify_modify = max(config['seconds_before_inotify_modify'], 1)
            
            for scan in config['scans']:
                plex_library: str = ''
                if 'plex_library' in scan:
                    plex_library = scan['plex_library']
                        
                emby_library: str = ''
                if 'emby_library' in scan:
                    emby_library = scan['emby_library']
                        
                jellyfin_library: str = ''
                if 'jellyfin_library' in scan:
                    jellyfin_library = scan['jellyfin_library']
                
                scan_config = ScanConfigInfo(scan['name'], plex_library, emby_library, jellyfin_library, 0.0)
                
                for path in scan['paths']:
                    scan_config.paths.append(path['container_path'])
                
                self.scan_configs.append(scan_config)
            
            for folder in config['ignore_folder_with_name']:
                self.ignore_folder_with_name.append(folder['ignore_folder'])
                
            if config['valid_file_extensions'] != '':
                self.valid_file_extensions = config['valid_file_extensions'].split(',')
                
        except Exception as e:
            self.log_error('Read config {}'.format(get_tag('error', e)))
    
    def shutdown(self):
        self.stop_threads = True
        
        temp_file_path = '/temp.txt'
        
        # Create a temp file to notify the inotify adapters
        for scan in self.scan_configs:
            for path in scan.paths:
                temp_file = path + temp_file_path
                with open(temp_file, 'w') as file:
                    file.write('BREAK')
                    break
            
        # allow time for the events
        time.sleep(1)
        
        with self.monitor_lock:
            self.monitors.clear()
                            
        # clean up the temp files
        for scan in self.scan_configs:
            for path in scan.paths:
                temp_file = path + temp_file_path
                os.remove(temp_file)
                break
        
        self.log_info('Successful shutdown')
    
    def _get_scan_path_valid(self, path: str) -> bool:
        for folder_name in self.ignore_folder_with_name:
            if folder_name in path:
                return False
        return True
    
    def _get_scan_extension_valid(self, filename: str) -> bool:
        if len(self.valid_file_extensions) > 0:
            for valid_extension in self.valid_file_extensions:
                if filename.endswith(valid_extension):
                    return True
            return False
        else:
            # No valid file extensions defined so all extensions are valid
            return True
    
    def _notify_plex(self, plex_library_name: str) -> bool:
        if plex_library_name != '':
            plex_valid = self.plex_api.get_valid()
            if plex_valid == True:
                if self.plex_api.get_library(plex_library_name) != self.plex_api.get_invalid_type():
                    self.plex_api.set_library_scan(plex_library_name)
                    return True
                else:
                    self.log_warning('{} {} not found on server'.format(get_formatted_plex(), get_tag('library', plex_library_name)))
            else:
                self.log_warning('{} server not available'.format(get_formatted_plex()))
        return False
    
    def _notify_emby(self, emby_library_name: str) -> bool:
        if emby_library_name != '':
            if self.emby_api.get_valid() == True:
                library_id = self.emby_api.get_library_id(emby_library_name)
                if library_id != self.emby_api.get_invalid_item_id():
                    self.emby_api.set_library_scan(library_id)
                    return True
                else:
                    self.log_warning('{} {} not found on server'.format(get_formatted_emby(), get_tag('library', emby_library_name)))
            else:
                self.log_warning('{} server not available'.format(get_formatted_emby()))
        return False
    
    def _notify_jellyfin(self, jellyfin_library_name: str) -> bool:
        if jellyfin_library_name != '':
            if self.jellyfin_api.get_valid() == True:
                library_id = self.jellyfin_api.get_library_id(jellyfin_library_name)
                if library_id != self.jellyfin_api.get_invalid_item_id():
                    self.jellyfin_api.set_library_scan(library_id)
                    return True
                else:
                    self.log_warning('{} {} not found on server'.format(get_formatted_jellyfin(), get_tag('library', jellyfin_library_name)))
            else:
                self.log_warning('{} server not available'.format(get_formatted_jellyfin()))
        return False
    
    def _notify_media_servers(self, scan_config: ScanConfigInfo):
        # all the libraries in this monitor group are identical so only one scan is required
        target = ''
        if self._notify_plex(scan_config.plex_library) == True:
            target = build_target_string(target, get_formatted_plex(), scan_config.plex_library)
        if self._notify_emby(scan_config.emby_library) == True:
            target = build_target_string(target, get_formatted_emby(), scan_config.emby_library)
        if self._notify_jellyfin(scan_config.jellyfin_library) == True:
            target = build_target_string(target, get_formatted_jellyfin(), scan_config.jellyfin_library)
        
        # Loop through all the paths in this monitor and log that it has been sent to the target
        if target != '':
            for path in scan_config.paths:
                self.log_info('✅ Monitor moved to target {} {}'.format(target, get_tag('path', path)))
    
    def _get_all_paths_in_path(self, path: str) -> List[str]:
        return_paths: list[str] = []

        try:
            q = [path]
            while q:
                current_path = q[0]
                del q[0]

                return_paths.append(current_path)

                for filename in os.listdir(current_path):
                    entry_filepath = os.path.join(current_path, filename)
                    if os.path.isdir(entry_filepath) is False:
                        continue

                    q.append(entry_filepath)
        
        except Exception as e:
            self.log_error('_get_all_paths_in_path {}'.format(get_tag('error', e)))
            
        return return_paths
    
    def _add_inotify_watch(self, i: adapters.Inotify, path: str, scan_mask: int):
        # Add the path and all sub-paths to the notify list
        new_paths = self._get_all_paths_in_path(path)
        
        try:
            current_path = ''
            with self.watched_paths_lock:
                for new_path in new_paths:
                    new_path_in_watched = new_path in self.watched_paths
                    if new_path_in_watched == False:
                        current_path = new_path
                        i.add_watch(new_path, scan_mask)
                        self.watched_paths.append(new_path)
        except Exception as e:
            self.log_error('_add_inotify_watch {} {}'.format(get_tag('path', current_path), get_tag('error', e)))
    
    def _delete_inotify_watch(self, i: adapters.Inotify, path: str):
        # inotify automatically deletes watches of deleted paths
        # cleanup our local path list when a path is deleted
        with self.watched_paths_lock:
            current_path = ''
            try:
                if path in self.watched_paths:
                    new_monitor_paths: list[str] = []
                    for watch_path in self.watched_paths:
                        current_path = watch_path
                        if watch_path.startswith(path) == True:
                            wd = i.get_watch_id(watch_path)
                            if wd is not None and wd >= 0:
                                i.remove_watch(watch_path, True)
                        else:
                            new_monitor_paths.append(watch_path)

                    self.watched_paths = new_monitor_paths
            except Exception as e:
                self.log_warning('_delete_inotify_watch {} {}'.format(get_tag('path', current_path), get_tag('error', e)))
        
    def _monitor(self):
        while self.stop_threads == False:
            # Process any monitors currently in the system
            with self.monitor_lock:
                if len(self.monitors) > 0:
                    current_time = time.time()
                    if current_time - self.last_notify_time >= self.seconds_between_notifies:
                        current_monitor = None
                        for monitor in self.monitors:
                            if (current_time - monitor.time) >= self.seconds_before_notify:
                                current_monitor = monitor
                                self.last_notify_time = current_time
                                break
                            
                        # A monitor was finished and servers notified remove it from the list
                        if current_monitor is not None:
                            # If servers were just notified for this name remove all monitors for the same name since
                            # the server refresh is by library not by item
                            new_monitors: list[ScanConfigInfo] = []
                            for monitor in self.monitors:
                                if monitor.name != current_monitor.name:
                                    new_monitors.append(monitor)

                            self._notify_media_servers(current_monitor)
                            self.monitors = new_monitors
            
            # Check if any new paths need to be added to the inotify list
            with self.check_new_paths_lock:
                if len(self.check_new_paths) > 0:
                    new_path_list: list[CheckPathData] = []
                    current_time = time.time()
                    for check_path in self.check_new_paths:
                        if (current_time - check_path.time) >= self.seconds_before_inotify_modify:
                            if check_path.deleted == True:
                                self._delete_inotify_watch(check_path.i, check_path.path)
                            else:
                                # Make sure the path still exists before continue
                                if os.path.isdir(check_path.path) == True:
                                    self._add_inotify_watch(check_path.i, check_path.path, check_path.scan_mask)
                        else:
                            new_path_list.append(check_path)
                
                        # Set the check new paths to the new list
                        self.check_new_paths = new_path_list
                
            time.sleep(self.seconds_monitor_rate)
        
        self.log_info('Stopping monitor thread')
    
    def _log_scan_moved_to_monitor(self, name: str, path: str):
        self.log_info('➡️ Scan moved to monitor {} {}'.format(get_tag('name', name), get_tag('path', path)))
        
    def _add_file_monitor(self, path: str, scan: ScanConfigInfo):
        monitor_found = False
        current_time = time.time()
        
        # Check if this path or library already exists in the list
        #   If the library already exists just update the time to wait since we can only notify per library to update not per item
        with self.monitor_lock:
            for monitor in self.monitors:
                # If the name is the same this monitor belongs to the same library so update the time
                if monitor.name == scan.name:
                    monitor_found = True
                    
                    path_in_monitor = False
                    for monitor_path in monitor.paths:
                        if monitor_path == path:
                            path_in_monitor = True
                            break
                    
                    if path_in_monitor == False:
                        monitor.paths.append(path)
                        self._log_scan_moved_to_monitor(monitor.name, path)

                    monitor.time = current_time
        
        # No monitor found for this item add it to the monitor list
        if monitor_found == False:
            monitor_info = ScanConfigInfo(scan.name, scan.plex_library, scan.emby_library, scan.jellyfin_library, current_time)
            monitor_info.paths.append(path)
            with self.monitor_lock:
                self.monitors.append(monitor_info)
            self._log_scan_moved_to_monitor(monitor_info.name, path)
        
    def _monitor_path(self, scan: ScanConfigInfo):
        scanner_mask =  (constants.IN_MODIFY | constants.IN_MOVED_FROM | constants.IN_MOVED_TO | 
                        constants.IN_CREATE | constants.IN_DELETE)
        
        # Setup the inotify watches for the current folder and all sub-folders
        i = adapters.Inotify(self.logger)
            
        for scan_path in scan.paths:
            self.log_info('Starting monitor {} {}'.format(get_tag('name', scan.name), get_tag('path', scan_path)))
            self._add_inotify_watch(i, scan_path, scanner_mask)
            
        for event in i.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event
            if filename != '':
                # Make sure this is valid path to monitor
                if self._get_scan_path_valid(path) == True:
                    # New path check. This will add or delete scans if folders are added or removed
                    if 'IN_ISDIR' in type_names:
                        is_delete = 'IN_DELETE' in type_names or 'IN_MOVED_FROM' in type_names
                        if 'IN_CREATE' in type_names or 'IN_MOVED_TO' in type_names or is_delete == True:
                            with self.check_new_paths_lock:
                                self.check_new_paths.append(CheckPathData('{}/{}'.format(path, filename), i, scanner_mask, time.time(), is_delete))
                
                    # If the extension is valid add the file monitor
                    if self._get_scan_extension_valid(filename) == True:
                        self._add_file_monitor(path, scan)
            
            if self.stop_threads == True:
                for scan_path in scan.paths:
                    self.log_info('Stopping watch {} {}'.format(get_tag('name', scan.name), get_tag('path', scan_path)))
                break
        
    def start(self):
        for scan in self.scan_configs:
            thread = Thread(target=self._monitor_path, args=(scan,)).start()
            self.threads.append(thread)
        
        self.monitor_thread = Thread(target=self._monitor, args=()).start()
        
    def init_scheduler_jobs(self):
        self.start()
