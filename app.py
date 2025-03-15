"""
Remotescan: A media server library scanner and notification tool.

Remotescan monitors specified directories for changes (new files, deletions, etc.)
and triggers library scans on media servers like Plex, Emby, and Jellyfin.

Key Components:
    - ApiManager: Handles communication with media server APIs.
    - Remotescan Service: Monitors file system changes and triggers server scans.
    - BlockingScheduler: Manages scheduled tasks.
    - LogManager: Handles logging to files and console.

Configuration:
    Remotescan is configured via a JSON file specified by the CONFIG_PATH
    environment variable.

Usage:
    1. Set the CONFIG_PATH environment variable to the location of your
       configuration file.
    2. Run the app.py script.
"""

REMOTE_SCAN_VERSION: str = "v2.1.0"

import sys
import os
import json
import signal
import time
from sys import platform
from typing import Any

from apscheduler.schedulers.blocking import BlockingScheduler

from api.api_manager import ApiManager
from common.log_manager import LogManager
from common import utils
from service.ServiceBase import ServiceBase

if platform == "linux":
    from service.Remotescan import Remotescan

# Global Variables
api_manager: ApiManager = None
log_manager = LogManager(__name__)
scheduler = BlockingScheduler()

# Available Services
services: list[ServiceBase] = []
##########################

def handle_sigterm(signum: int, frame: Any):
    """Handles the SIGTERM signal for graceful shutdown."""
    log_manager.get_logger().info("SIGTERM received, shutting down ...")
    for service in services:
        service.shutdown()
    scheduler.shutdown(wait=True)
    sys.exit(0)

def _create_services(data: dict):
    """Creates and returns a list of services based on the configuration."""
    if platform == "linux":
        if "remote_scan" in data:
            services.append(
                Remotescan(
                    api_manager,
                    data["remote_scan"],
                    log_manager.get_logger(),
                    scheduler
                )
            )
        else:
            log_manager.get_logger().error(
                "Configuration file problem no remote_scan data found!"
            )

def _do_nothing() -> None:
    """A dummy function to keep the scheduler alive."""
    time.sleep(1)
    
conf_loc_path_file: str = ""
config_file_valid: bool = True
if "CONFIG_PATH" in os.environ:
    conf_loc_path_file = os.environ["CONFIG_PATH"].rstrip("/")
else:
    config_file_valid = False

if config_file_valid and os.path.exists(conf_loc_path_file):
    try:
        # Load the configuration file
        with open(conf_loc_path_file, "r") as f:
            data: dict = json.load(f)

        # Set up signal termination handle
        signal.signal(signal.SIGTERM, handle_sigterm)

        # Configure the gotify logging
        log_manager.configure_gotify(data)
        
        log_manager.get_logger().info(
            f"Starting Remotescan {REMOTE_SCAN_VERSION}"
        )
        
        # Create the API Manager
        api_manager = ApiManager(data, log_manager.get_logger())

        # Create the services
        _create_services(data)
        
        # Init the services
        for service in services:
            service.init_scheduler_jobs()
        
        if len(services) > 0:
            # Add a job to do nothing to keep the script alive
            scheduler.add_job(
                _do_nothing,
                trigger="interval",
                hours=24
            )

            # Start the scheduler for all jobs
            scheduler.start()
    
    except FileNotFoundError as e:
        log_manager.get_logger().error(
            f"Config file not found: {utils.get_tag('error', e)}"
        )
    except json.JSONDecodeError as e:
        log_manager.get_logger().error(
            f"Error decoding JSON in config file: {utils.get_tag('error', e)}"
        )
    except KeyError as e:
        log_manager.get_logger().error(
            f"Missing key in config file: {utils.get_tag('error', e)}"
        )
    except Exception as e:
        log_manager.get_logger().error(
            f"An unexpected error occurred: {utils.get_tag('error', e)}"
        )
else:
    log_manager.get_logger().error(
        f"Error finding config file {conf_loc_path_file}\n"
    )

# END Main script run