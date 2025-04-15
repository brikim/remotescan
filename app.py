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

from sys import platform
import time
import signal
import json
import os
import sys

from apscheduler.schedulers.blocking import BlockingScheduler

from api.api_manager import ApiManager
from common import utils
from common.log_manager import LogManager
from service.service_base import ServiceBase
if platform == "linux":
    from service.remote_scan import Remotescan

REMOTE_SCAN_VERSION: str = "v3.1.2"

# Global Variables
api_manager: ApiManager = None
log_manager = LogManager(__name__)
scheduler = BlockingScheduler()

# Available Services
services: list[ServiceBase] = []
##########################


def handle_sigterm(_sig, _frame):
    """Handles the SIGTERM signal for graceful shutdown."""
    log_manager.log_info("SIGTERM received, shutting down ...")
    for service_base in services:
        service_base.shutdown()
    scheduler.shutdown(wait=True)
    sys.exit(0)


def _create_services(config: dict):
    """Creates and returns a list of services based on the configuration."""
    if platform == "linux":
        if "remote_scan" in config:
            services.append(
                Remotescan(
                    api_manager,
                    config["remote_scan"],
                    log_manager,
                    scheduler
                )
            )
        else:
            log_manager.log_error(
                "Configuration file problem no remote_scan data found!"
            )


def _do_nothing() -> None:
    """A dummy function to keep the scheduler alive."""
    time.sleep(1)


conf_loc_path_file: str = ""
config_path_valid: bool = "CONFIG_PATH" in os.environ
if config_path_valid:
    conf_loc_path_file = os.environ["CONFIG_PATH"].rstrip("/")
    if os.path.exists(conf_loc_path_file):
        try:
            # Load the configuration file
            with open(conf_loc_path_file, "r", encoding="utf-8") as f:
                data: dict = json.load(f)

            # Set up signal termination handle
            signal.signal(signal.SIGTERM, handle_sigterm)

            # Configure the gotify logging
            log_manager.configure_gotify(data)

            log_manager.log_info(
                f"Starting Remotescan {REMOTE_SCAN_VERSION}"
            )

            # Create the API Manager
            api_manager = ApiManager(data, log_manager)

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
            log_manager.log_error(
                f"Config file not found: {utils.get_tag('error', e)}"
            )
        except json.JSONDecodeError as e:
            log_manager.log_error(
                f"Error decoding JSON in config file: {utils.get_tag('error', e)}",
            )
        except KeyError as e:
            log_manager.log_error(
                f"Missing key in config file: {utils.get_tag('error', e)}"
            )
        except Exception as e:
            log_manager.log_error(
                f"An unexpected error occurred: {utils.get_tag('error', e)}"
            )
    else:
        log_manager.log_error(
            f"Error finding config file {conf_loc_path_file}"
        )
else:
    log_manager.log_error("Environment variable CONFIG_PATH not found")

# END Main script run
