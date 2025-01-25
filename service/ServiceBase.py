
from common.utils import get_tag, get_log_header

class ServiceBase:
    def __init__(self, logger, scheduler):
        self.logger = logger
        self.scheduler = scheduler
    
    def _log_msg(self, type, message):
        if type == 'warning':
            self.logger.warning(message)
        elif type == 'error':
            self.logger.error(message)
        else:
            self.logger.info(message)

    def log_info(self, message):
        self._log_msg('info', message)
    
    def log_info(self, message):
        self._log_msg('info', message)
        
    def log_warning(self, message):
        self._log_msg('warning', message)
        
    def log_error(self, message):
        self._log_msg('error', message)
    
    def log_service_enabled(self):
        self.log_info('Enabled')
        
    def init_scheduler_jobs(self):
        pass
    
    def shutdown(self):
        pass
