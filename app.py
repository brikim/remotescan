"""
Autoscan
"""

version = 'v1.2.0'

import sys
import os
import json
import logging
import colorlog
import signal
import time
from sys import platform
from typing import List
from logging.handlers import RotatingFileHandler
from apscheduler.schedulers.blocking import BlockingScheduler

from api.plex import PlexAPI
from api.emby import EmbyAPI
from api.jellyfin import JellyfinAPI

from common.gotify_handler import GotifyHandler
from common.plain_text_formatter import PlainTextFormatter
from common.gotify_plain_text_formatter import GotifyPlainTextFormatter

from common.utils import get_tag, get_formatted_emby, get_formatted_plex, get_formatted_jellyfin

from service.ServiceBase import ServiceBase
if platform == "linux":
    from service.AutoScan import AutoScan

# Global Variables #######
logger = logging.getLogger(__name__)
scheduler = BlockingScheduler()

# Api
plex_api: PlexAPI = None
emby_api: EmbyAPI = None
jellyfin_api: JellyfinAPI = None

# Available Services
services: list[ServiceBase] = []
##########################

def handle_sigterm(signum, frame):
    logger.info('SIGTERM received, shutting down ...')
    for service in services:
        service.shutdown()
    scheduler.shutdown(wait=True)
    sys.exit(0)

def do_nothing():
    time.sleep(1)

conf_loc_path_file: str = ''
config_file_valid = True
if "CONFIG_PATH" in os.environ:
    conf_loc_path_file = os.environ['CONFIG_PATH'].rstrip('/')
else:
    config_file_valid = False

if config_file_valid == True and os.path.exists(conf_loc_path_file) == True:
    try:
        # Opening JSON file
        f = open(conf_loc_path_file, 'r')
        data = json.load(f)

        # Main script run ####################################################

        # Set up signal termination handle
        signal.signal(signal.SIGTERM, handle_sigterm)

        #date format
        date_format = '%Y-%m-%d %H:%M:%S'

        # Set up the logger
        logger.setLevel(logging.INFO)
        formatter = PlainTextFormatter()
        
        # Create a file handler to write logs to a file
        rotating_handler = RotatingFileHandler('/logs/autoscan.log', maxBytes=50000, backupCount=5)
        rotating_handler.setLevel(logging.INFO)
        rotating_handler.setFormatter(formatter)

        log_colors = {
            'DEBUG': 'cyan',
            'INFO': 'light_green',
            'WARNING': 'light_yellow',
            'ERROR': 'light_red',
            'CRITICAL': 'bold_red'}

        # Create a stream handler to print logs to the console
        console_info_handler = colorlog.StreamHandler()
        console_info_handler.setLevel(logging.INFO)
        console_info_handler.setFormatter(colorlog.ColoredFormatter(
            '%(white)s%(asctime)s %(light_white)s- %(log_color)s%(levelname)s %(light_white)s- %(message)s', date_format, log_colors=log_colors))

        gotify_formatter = None
        gotify_handler = None
        if 'gotify_logging' in data and 'enabled' in data['gotify_logging'] and data['gotify_logging']['enabled'] == 'True':
            gotify_formatter = GotifyPlainTextFormatter()
            gotify_handler = GotifyHandler(data['gotify_logging']['url'], data['gotify_logging']['app_token'], data['gotify_logging']['message_title'], data['gotify_logging']['priority'])
            gotify_handler.setLevel(logging.WARNING)
            gotify_handler.setFormatter(gotify_formatter)
            
        # Add the handlers to the logger
        logger.addHandler(rotating_handler)
        logger.addHandler(console_info_handler)
        if gotify_handler is not None:
            logger.addHandler(gotify_handler)
        
        logger.info('Starting Autoscan {} *************************************'.format(version))
        
        # Create all the api servers
        if 'plex_url' in data and 'plex_api_key' in data:
            plex_api = PlexAPI(data['plex_url'], data['plex_api_key'], logger)
            if plex_api.get_valid() == False:
                logger.warning('{} server not available. Is this correct {} {}'.format(get_formatted_plex(), get_tag('url', data['plex_url']), get_tag('api_key', data['plex_api_key'])))
        elif 'plex_url' in data or 'plex_api_key' in data:
            logger.warning('{} configuration error must define both plex_url and plex_api_key'.format(get_formatted_plex()))
            
        
        if 'emby_url' in data and 'emby_api_key' in data:
            emby_api = EmbyAPI(data['emby_url'], data['emby_api_key'], logger)
            if emby_api.get_valid() == False:
                logger.warning('{} server not available. Is this correct {} {}'.format(get_formatted_emby(), get_tag('url', data['emby_url']), get_tag('api_key', data['emby_api_key'])))
        elif 'emby_url' in data or 'emby_api_key' in data:
            logger.warning('{} configuration error must define both emby_url and emby_api_key'.format(get_formatted_emby()))
                
        if 'jellyfin_url' in data and 'jellyfin_api_key' in data:
            jellyfin_api = JellyfinAPI(data['jellyfin_url'], data['jellyfin_api_key'], logger)
            if jellyfin_api.get_valid() == False:
                logger.warning('{} server not available. Is this correct {} {}'.format(get_formatted_jellyfin(), get_tag('url', data['jellyfin_url']), get_tag('api_key', data['jellyfin_api_key'])))
        elif 'jellyfin_url' in data or 'jellyfin_api_key' in data:
            logger.warning('{} configuration error must define both jellyfin_url and jellyfin_api_key'.format(get_formatted_jellyfin()))
        
        # Create the services ####################################
        
        # Create the AutoScan Service
        if platform == 'linux':
            if 'auto_scan' in data:
                services.append(AutoScan(plex_api, emby_api, jellyfin_api, data['auto_scan'], logger, scheduler))
            else:
                logger.error('Configuration file problem no auto_scan data found!')
        
        # ########################################################
        
        # Init the services ######################################
        for service in services:
            service.init_scheduler_jobs()
        # ########################################################
        
        if len(services) > 0:
            # Add a job to do nothing to keep the script alive
            scheduler.add_job(do_nothing, trigger='interval', hours=24)

            # Start the scheduler for all jobs
            scheduler.start()
        
    except Exception as e:
        logger.error("Error starting Autoscan: {}".format(e))
else:
    sys.stderr.write("Error opening config file {}\n".format(conf_loc_path_file))

# END Main script run ####################################################