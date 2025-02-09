
import os
import time
import threading

from threading import Thread
from dataclasses import dataclass, field
from logging import Logger
from apscheduler.schedulers.blocking import BlockingScheduler
from external.PyInotify.inotify import adapters, constants
from typing import Any

from api.plex import PlexAPI
from api.emby import EmbyAPI
from api.jellyfin import JellyfinAPI

from service.ServiceBase import ServiceBase

from common import utils

@dataclass
class ScanConfigInfo:
    name: str
    plex_library: str
    emby_library: str
    jellyfin_library: str
    time: float
    paths: list[str] = field(default_factory=list)

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
        
        self.threads: list[Thread] = []
        self.stop_threads = False
        
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
            self._log_error('Read config {}'.format(utils.get_tag('error', e)))
    
    def __get_scan_path_valid(self, path: str) -> bool:
        for folder_name in self.ignore_folder_with_name:
            if folder_name in path:
                return False
        return True
    
    def __get_scan_extension_valid(self, filename: str) -> bool:
        if len(self.valid_file_extensions) > 0:
            for valid_extension in self.valid_file_extensions:
                if filename.endswith(valid_extension):
                    return True
        else:
            # No valid file extensions defined so all extensions are valid
            return True
        return False
    
    def __notify_plex(self, plex_library_name: str) -> bool:
        if plex_library_name != '':
            plex_valid = self.plex_api.get_valid()
            if plex_valid is True:
                if self.plex_api.get_library(plex_library_name) != self.plex_api.get_invalid_type():
                    self.plex_api.set_library_scan(plex_library_name)
                    return True
                else:
                    self._log_warning('{} {} not found on server'.format(utils.get_formatted_plex(), utils.get_tag('library', plex_library_name)))
            else:
                self._log_warning('{} server not available'.format(utils.get_formatted_plex()))
        return False
    
    def __notify_emby(self, emby_library_name: str) -> bool:
        if emby_library_name != '':
            if self.emby_api.get_valid() is True:
                library_id = self.emby_api.get_library_id(emby_library_name)
                if library_id != self.emby_api.get_invalid_item_id():
                    self.emby_api.set_library_scan(library_id)
                    return True
                else:
                    self._log_warning('{} {} not found on server'.format(utils.get_formatted_emby(), utils.get_tag('library', emby_library_name)))
            else:
                self._log_warning('{} server not available'.format(utils.get_formatted_emby()))
        return False
    
    def __notify_jellyfin(self, jellyfin_library_name: str) -> bool:
        if jellyfin_library_name != '':
            if self.jellyfin_api.get_valid() is True:
                library_id = self.jellyfin_api.get_library_id(jellyfin_library_name)
                if library_id != self.jellyfin_api.get_invalid_item_id():
                    self.jellyfin_api.set_library_scan(library_id)
                    return True
                else:
                    self._log_warning('{} {} not found on server'.format(utils.get_formatted_jellyfin(), utils.get_tag('library', jellyfin_library_name)))
            else:
                self._log_warning('{} server not available'.format(utils.get_formatted_jellyfin()))
        return False
    
    def _notify_media_servers(self, scan_config: ScanConfigInfo):
        # all the libraries in this monitor group are identical so only one scan is required
        target = ''
        if self.__notify_plex(scan_config.plex_library) is True:
            target = utils.build_target_string(target, utils.get_formatted_plex(), scan_config.plex_library)
        if self.__notify_emby(scan_config.emby_library) is True:
            target = utils.build_target_string(target, utils.get_formatted_emby(), scan_config.emby_library)
        if self.__notify_jellyfin(scan_config.jellyfin_library) is True:
            target = utils.build_target_string(target, utils.get_formatted_jellyfin(), scan_config.jellyfin_library)
        
        # Loop through all the paths in this monitor and log that it has been sent to the target
        if target != '':
            for path in scan_config.paths:
                self._log_info('✅ Monitor moved to target {} {}'.format(target, utils.get_tag('path', path)))
        
    def __monitor(self):
        while self.stop_threads is False:
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
                
            time.sleep(self.seconds_monitor_rate)
        
        self._log_info('Stopping monitor thread')
    
    def __log_scan_moved_to_monitor(self, name: str, path: str):
        self._log_info('➡️ Scan moved to monitor {} {}'.format(utils.get_tag('name', name), utils.get_tag('path', path)))
        
    def __add_file_monitor(self, path: str, scan: ScanConfigInfo):
        monitor_found = False
        current_time = time.time()
        
        # Check if this path or library already exists in the list
        # If the library already exists just update the time to wait since we can only notify per library to update not per item
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
                    
                    if path_in_monitor is False:
                        monitor.paths.append(path)
                        self.__log_scan_moved_to_monitor(monitor.name, path)

                    monitor.time = current_time
        
        # No monitor found for this item add it to the monitor list
        if monitor_found is False:
            monitor_info = ScanConfigInfo(scan.name, scan.plex_library, scan.emby_library, scan.jellyfin_library, current_time)
            monitor_info.paths.append(path)
            with self.monitor_lock:
                self.monitors.append(monitor_info)
            self.__log_scan_moved_to_monitor(monitor_info.name, path)
        
    def __monitor_path(self, scan_config: ScanConfigInfo):
        scanner_mask =  (constants.IN_MODIFY | constants.IN_MOVED_FROM | constants.IN_MOVED_TO | 
                        constants.IN_CREATE | constants.IN_DELETE)
        
        # Make a copy of the paths to send to inotify since these will get deleted
        inotify_paths: list[str] = []
        for scan_path in scan_config.paths:
            self._log_info('Starting monitor {} {}'.format(utils.get_tag('name', scan_config.name), utils.get_tag('path', scan_path)))
            inotify_paths.append(scan_path)
        
        # Setup the inotify watches for the current folder and all sub-folders
        i = adapters.InotifyTrees(logger=self.logger, paths=inotify_paths, mask=scanner_mask)
            
        for event in i.event_gen(yield_nones=False):
            if self.stop_threads is True:
                for scan_path in scan_config.paths:
                    self._log_info('Stopping watch {} {}'.format(utils.get_tag('name', scan_config.name), utils.get_tag('path', scan_path)))
                break
            
            (_, type_names, path, filename) = event
            if filename != '':
                # Make sure this is valid path to monitor and the extension is valid add the file monitor
                if self.__get_scan_path_valid(path) is True and self.__get_scan_extension_valid(filename) is True:
                    self.__add_file_monitor(path, scan_config)
    
    def init_scheduler_jobs(self):
        for scan_config in self.scan_configs:
            thread = Thread(target=self.__monitor_path, args=(scan_config,)).start()
            self.threads.append(thread)
        
        self.monitor_thread = Thread(target=self.__monitor, args=()).start()
        
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
                            
        # clean up the temp files
        for scan in self.scan_configs:
            for path in scan.paths:
                temp_file = path + temp_file_path
                os.remove(temp_file)
                break
        
        with self.monitor_lock:
            self.monitors.clear()
        
        self._log_info('Successful shutdown')
