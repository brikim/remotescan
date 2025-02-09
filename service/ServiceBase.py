
from logging import Logger
from apscheduler.schedulers.blocking import BlockingScheduler

class ServiceBase:
    def __init__(self, logger: Logger, scheduler: BlockingScheduler):
        self.logger = logger
        self.scheduler = scheduler
    
    def __log_msg(self, type: str, message: str):
        if type == 'warning':
            self.logger.warning(message)
        elif type == 'error':
            self.logger.error(message)
        else:
            self.logger.info(message)

    def _log_info(self, message: str):
        self.__log_msg('info', message)
        
    def _log_warning(self, message: str):
        self.__log_msg('warning', message)
        
    def _log_error(self, message: str):
        self.__log_msg('error', message)
        
    def init_scheduler_jobs(self):
        pass
    
    def shutdown(self):
        pass
