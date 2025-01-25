
from common.utils import get_cron_from_string, get_tag, get_log_header

class ServiceBase:
    def __init__(self, ansi_code, service_name, config, logger, scheduler):
        self.logger = logger
        self.scheduler = scheduler
        self.cron = None
        self.log_header = get_log_header(ansi_code, service_name)
        
        if 'cron_run_rate' in config:
            self.cron = get_cron_from_string(config['cron_run_rate'], self.logger, self.__module__)
    
    def _log_msg(self, type, message):
        if type == 'warning':
            self.logger.warning('{} {}'.format(self.log_header, message))
        elif type == 'error':
            self.logger.error('{} {}'.format(self.log_header, message))
        else:
            self.logger.info('{} {}'.format(self.log_header, message))

    def log_info(self, message):
        self._log_msg('info', message)
    
    def log_info(self, message):
        self._log_msg('info', message)
        
    def log_warning(self, message):
        self._log_msg('warning', message)
        
    def log_error(self, message):
        self._log_msg('error', message)
    
    def log_service_enabled(self):
        if self.cron is not None:
            self.log_info('Enabled - Running every {} {}'.format(get_tag('hour', self.cron.hours), get_tag('minute', self.cron.minutes)))
        else:
            self.log_info('Enabled')
        
    def init_scheduler_jobs(self):
        pass
    
    def shutdown(self):
        pass
