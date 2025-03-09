
from logging import Logger
from apscheduler.schedulers.blocking import BlockingScheduler

class ServiceBase:
    def __init__(
        self,
        logger: Logger,
        scheduler: BlockingScheduler
    ):
        self.logger = logger
        self.scheduler = scheduler
    
    def _log_info(self, message: str):
        self.logger.info(message)
        
    def _log_warning(self, message: str):
        self.logger.warning(message)
        
    def _log_error(self, message: str):
        self.logger.error(message)
        
    def init_scheduler_jobs(self):
        pass
    
    def shutdown(self):
        pass
