
""" Remote Scan service monitors configured folders and notifies media servers."""

import os
from sys import platform
import time
import threading

from threading import Thread, Condition
from dataclasses import dataclass, field
from apscheduler.schedulers.blocking import BlockingScheduler

from api.api_manager import ApiManager
from common import utils
from common.log_manager import LogManager
from service.service_base import ServiceBase
if platform == "linux":
    import external.PyInotify.inotify.adapters
    import external.PyInotify.inotify.constants


@dataclass
class ServerLibraryConfigInfo:
    """Structure for holding library configuration information. """
    server_name: str
    library: str


@dataclass
class ScanConfigInfo:
    """Structure for holding scan configuration information. """
    name: str
    time: float
    plex_library_list: list[ServerLibraryConfigInfo] = field(
        default_factory=list)
    emby_library_list: list[ServerLibraryConfigInfo] = field(
        default_factory=list)
    jellyfin_library_list: list[ServerLibraryConfigInfo] = field(
        default_factory=list)
    paths: list[str] = field(default_factory=list)


class Remotescan(ServiceBase):
    """Remotescan Service"""

    def __init__(
        self,
        api_manager: ApiManager,
        config: dict,
        log_manager: LogManager,
        scheduler: BlockingScheduler
    ):
        super().__init__(log_manager, scheduler)

        self.api_manager = api_manager

        self.ignore_folder_list: list[str] = []
        self.valid_file_extension_list: list[str] = []

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
        self.stop_threads: bool = False
        self.monitor_condition = threading.Condition()

        if "seconds_monitor_rate" in config:
            self.seconds_monitor_rate = max(
                config["seconds_monitor_rate"], 1
            )
        if "seconds_before_notify" in config:
            self.seconds_before_notify = max(
                config["seconds_before_notify"], 30
            )
        if "seconds_between_notifies" in config:
            self.seconds_between_notifies = max(
                config["seconds_between_notifies"], 10
            )
        if "seconds_before_inotify_modify" in config:
            self.seconds_before_inotify_modify = max(
                config["seconds_before_inotify_modify"], 1
            )
        for scan in config["scans"]:
            scan_name = "Not Configured"
            if "name" in scan:
                scan_name = scan["name"]
            else:
                self._log_warning(
                    f"Missing {utils.get_tag("tag", "name")} from scan configuration")

            scan_config = ScanConfigInfo(
                scan_name,
                0.0
            )

            if "plex" in scan:
                for plex_server in scan["plex"]:
                    if "server_name" in plex_server and "library" in plex_server:
                        if plex_server["library"]:
                            scan_config.plex_library_list.append(
                                ServerLibraryConfigInfo(
                                    plex_server["server_name"],
                                    plex_server["library"]
                                )
                            )
                        else:
                            self._log_warning(
                                f"{utils.get_formatted_plex()} scan {utils.get_tag("attribute", "library")} blank ... Skipping"
                            )

            if "emby" in scan:
                for emby_server in scan["emby"]:
                    if "server_name" in emby_server and "library" in emby_server:
                        if emby_server["library"]:
                            scan_config.emby_library_list.append(
                                ServerLibraryConfigInfo(
                                    emby_server["server_name"],
                                    emby_server["library"]
                                )
                            )
                        else:
                            self._log_warning(
                                f"{utils.get_formatted_emby()} scan {utils.get_tag("attribute", "library")} blank ... Skipping"
                            )

            if "jellyfin" in scan:
                for jellyfin_server in scan["jellyfin"]:
                    if "server_name" in jellyfin_server and "library" in jellyfin_server:
                        if jellyfin_server["library"]:
                            scan_config.jellyfin_library_list.append(
                                ServerLibraryConfigInfo(
                                    jellyfin_server["server_name"],
                                    jellyfin_server["library"]
                                )
                            )
                        else:
                            self._log_warning(
                                f"{utils.get_formatted_jellyfin()} scan {utils.get_tag("attribute", "library")} blank ... Skipping"
                            )

            for path in scan["paths"]:
                scan_config.paths.append(path["container_path"])

            total_libraries = (
                len(scan_config.plex_library_list)
                + len(scan_config.emby_library_list)
                + len(scan_config.jellyfin_library_list)
            )
            if (
                total_libraries > 0
                and len(scan_config.paths) > 0
            ):
                self.scan_configs.append(scan_config)
            else:
                if total_libraries == 0:
                    self._log_warning(
                        f"No Media Server libraries for scan {utils.get_tag('name', scan_name)} ... Skipping"
                    )
                if len(scan_config.paths) == 0:
                    self._log_warning(
                        f"No paths for scan {utils.get_tag('name', scan_name)} ... Skipping"
                    )

        for folder in config["ignore_folders"]:
            self.ignore_folder_list.append(
                folder["ignore_folder"]
            )

        if config["valid_file_extensions"] != "":
            self.valid_file_extension_list = config["valid_file_extensions"].split(
                ",")

    def __get_scan_path_valid(self, path: str) -> bool:
        """ Get if the path is valid or should be ignored """
        for folder_name in self.ignore_folder_list:
            if folder_name in path:
                return False
        return True

    def __get_scan_extension_valid(self, filename: str) -> bool:
        """ Get if the filename contains a valid extension """
        if len(self.valid_file_extension_list) > 0:
            for valid_extension in self.valid_file_extension_list:
                if filename.endswith(valid_extension):
                    return True
        else:
            # No valid file extensions defined so all extensions are valid
            return True
        return False

    def __notify_plex(
        self,
        sever_config_info: ServerLibraryConfigInfo
    ) -> bool:
        """ Notify plex to scan the library """
        plex_api = self.api_manager.get_plex_api(
            sever_config_info.server_name
        )
        if plex_api is not None:
            if plex_api.get_valid():
                plex_api.set_library_scan(sever_config_info.library)
                return True
            else:
                self._log_warning(
                    f"{utils.get_formatted_plex()}({sever_config_info.server_name}) server not available ... Skipped notify for {utils.get_tag("library", sever_config_info.library)}"
                )
        return False

    def __notify_emby(
        self,
        sever_config_info: ServerLibraryConfigInfo
    ) -> bool:
        """ Notify the emby servers to scan the library """
        emby_api = self.api_manager.get_emby_api(
            sever_config_info.server_name
        )
        if emby_api is not None:
            if emby_api.get_valid():
                library_id = emby_api.get_library_id(
                    sever_config_info.library)
                if library_id != emby_api.get_invalid_type():
                    emby_api.set_library_scan(library_id)
                    return True
                else:
                    tag_library = utils.get_tag(
                        "library", sever_config_info.library)
                    self._log_warning(
                        f"{utils.get_formatted_emby()} {tag_library} not found on server"
                    )
            else:
                self._log_warning(
                    f"{utils.get_formatted_emby()}({sever_config_info.server_name}) server not available ... Skipped notify for {utils.get_tag("library", sever_config_info.library)}"
                )
        return False

    def __notify_jellyfin(
        self,
        sever_config_info: ServerLibraryConfigInfo
    ) -> bool:
        """ Notify the jellyfin servers to scan the library """
        jellyfin_api = self.api_manager.get_jellyfin_api(
            sever_config_info.server_name
        )
        if jellyfin_api is not None:
            if jellyfin_api.get_valid():
                library_id = jellyfin_api.get_library_id(
                    sever_config_info.library)
                if library_id != jellyfin_api.get_invalid_type():
                    jellyfin_api.set_library_scan(library_id)
                    return True
                else:
                    tag_library = utils.get_tag(
                        "library", sever_config_info.library)
                    self._log_warning(
                        f"{utils.get_formatted_jellyfin()} {tag_library} not found on server"
                    )
            else:
                self._log_warning(
                    f"{utils.get_formatted_jellyfin()}({sever_config_info.server_name}) server not available ... Skipped notify for {utils.get_tag("library", sever_config_info.library)}"
                )
        return False

    def __get_folder_name(self, path: str) -> str:
        """ Get the folder name from the path """
        last_index = path.rfind("/")
        if last_index == -1:
            return path
        return path[last_index + 1:]

    def __notify_media_servers(self, scan_config: ScanConfigInfo):
        """ Notify all the configured media servers to scan the library """
        # all the libraries in this monitor group are identical so only one scan is required
        target: str = ""
        for plex_library in scan_config.plex_library_list:
            if self.__notify_plex(plex_library):
                target = utils.build_target_string(
                    target,
                    utils.get_formatted_plex(),
                    plex_library.server_name
                )

        for emby_library in scan_config.emby_library_list:
            if self.__notify_emby(emby_library):
                target = utils.build_target_string(
                    target,
                    utils.get_formatted_emby(),
                    emby_library.server_name
                )

        for jellyfin_library in scan_config.jellyfin_library_list:
            if self.__notify_jellyfin(jellyfin_library):
                target = utils.build_target_string(
                    target,
                    utils.get_formatted_jellyfin(),
                    jellyfin_library.server_name
                )

        # Loop through all the paths in this monitor and log that it has been sent to the target
        if target:
            for path in scan_config.paths:
                self._log_info(
                    f"✅ Monitor moved to target {target} {utils.get_tag("folder", self.__get_folder_name(path))}"
                )

    def __monitor(self, condition: Condition):
        """ Thread to process new monitors """
        while not self.stop_threads:
            # If no monitors sleep until notified
            if len(self.monitors) == 0:
                with condition:
                    condition.wait()
                    
            # Process any monitors currently in the system
            with self.monitor_lock:
                if len(self.monitors) > 0:
                    current_time = time.time()
                    if current_time - self.last_notify_time >= self.seconds_between_notifies:
                        current_monitor: ScanConfigInfo = None
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

                            self.__notify_media_servers(current_monitor)
                            self.monitors = new_monitors

            time.sleep(self.seconds_monitor_rate)

        self._log_info("Stopping monitor thread")

    def __log_scan_moved_to_monitor(self, name: str, path: str):
        """ Log when a scan has moved to a monitor"""
        self._log_info(
            f"➡️ Scan moved to monitor {utils.get_tag('name', name)} {utils.get_tag("folder", self.__get_folder_name(path))}"
        )

    def __add_file_monitor(
        self,
        path: str,
        scan: ScanConfigInfo,
        monitor_condition: Condition
    ):
        """ Add a path to a monitor """
        monitor_found: bool = False
        current_time: float = time.time()

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

                    if not path_in_monitor:
                        monitor.paths.append(path)
                        self.__log_scan_moved_to_monitor(monitor.name, path)

                    monitor.time = current_time

        # No monitor found for this item add it to the monitor list
        if not monitor_found:
            monitor_info = ScanConfigInfo(
                scan.name,
                current_time
            )
            monitor_info.plex_library_list = scan.plex_library_list
            monitor_info.emby_library_list = scan.emby_library_list
            monitor_info.jellyfin_library_list = scan.jellyfin_library_list
            monitor_info.paths.append(path)
            with self.monitor_lock:
                self.monitors.append(monitor_info)
                with monitor_condition:
                    monitor_condition.notify()

            self.__log_scan_moved_to_monitor(monitor_info.name, path)

    def __monitor_path(
        self,
        scan_config: ScanConfigInfo,
        monitor_condition: Condition
    ):
        """ Setup the monitor for a scan configuration """
        scanner_mask = (
            external.PyInotify.inotify.constants.IN_MODIFY | external.PyInotify.inotify.constants.IN_MOVED_FROM
            | external.PyInotify.inotify.constants.IN_MOVED_TO | external.PyInotify.inotify.constants.IN_CREATE
            | external.PyInotify.inotify.constants.IN_DELETE
        )

        # Make a copy of the paths to send to inotify since these will get deleted
        inotify_paths: list[str] = []
        for scan_path in scan_config.paths:
            self._log_info(
                f"Starting monitor {utils.get_tag("name", scan_config.name)} {utils.get_tag("path", scan_path)}"
            )
            inotify_paths.append(scan_path)

        # Setup the inotify watches for the current folder and all sub-folders
        i = external.PyInotify.inotify.adapters.InotifyTrees(
            logger=self.log_manager.get_logger(),
            paths=inotify_paths,
            mask=scanner_mask
        )

        for event in i.event_gen(yield_nones=False):
            if self.stop_threads:
                for scan_path in scan_config.paths:
                    self._log_info(
                        f"Stopping watch {utils.get_tag("name", scan_config.name)} {utils.get_tag("path", scan_path)}"
                    )
                break

            (_, _type_names, path, filename) = event
            if filename != "":
                # Make sure this is valid path to monitor and the extension is valid add the file monitor
                if (
                    self.__get_scan_path_valid(path)
                    and self.__get_scan_extension_valid(filename)
                ):
                    self.__add_file_monitor(path, scan_config, monitor_condition)

    def init_scheduler_jobs(self):
        for scan_config in self.scan_configs:
            thread = Thread(
                target=self.__monitor_path,
                args=(scan_config, self.monitor_condition,)
            )
            thread.start()

            self.threads.append(thread)

        # Start the monitor thread
        # This thread is responsible for running at a periodic rate
        # and processing monitors added to the watch
        self.monitor_thread = Thread(
            target=self.__monitor,
            args=(self.monitor_condition,)
        )
        self.monitor_thread.start()

    def shutdown(self):
        """ Shutdown all monitors and threads """
        self.stop_threads = True
        
        with self.monitor_condition:
            self.monitor_condition.notify()

        # Create a temp file to notify the inotify adapters
        temp_file_path = "/temp.txt"
        for scan in self.scan_configs:
            for path in scan.paths:
                temp_file = f"{path}{temp_file_path}"
                with open(temp_file, "w", encoding="utf-8") as file:
                    file.write("BREAK")
                    break

        # allow time for the events
        time.sleep(1)

        # clean up the temp files
        for scan in self.scan_configs:
            for path in scan.paths:
                temp_file = f"{path}{temp_file_path}"
                os.remove(temp_file)
                break

        with self.monitor_lock:
            self.monitors.clear()

        self._log_info("Successful shutdown")
