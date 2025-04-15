""" Base class for all services in the application. """

from apscheduler.schedulers.blocking import BlockingScheduler

from common.log_manager import LogManager

class ServiceBase:
    """
    Base class for services in the application.

    Provides common logging functionality and a basic interface for
    initializing and shutting down services.
    """

    def __init__(
        self,
        log_manager: LogManager,
        scheduler: BlockingScheduler,
    ):
        """Initializes the ServiceBase with a log_manager and scheduler."""
        self.log_manager = log_manager
        self.scheduler = scheduler

    def _log_info(self, message: str):
        """ Log an info message. """
        self.log_manager.log_info(message)

    def _log_warning(self, message: str):
        """ Log an warning message. """
        self.log_manager.log_warning(message)

    def _log_error(self, message: str):
        """ Log an error message. """
        self.log_manager.log_error(message)

    def init_scheduler_jobs(self):
        """Initializes any scheduler jobs for the service."""

    def shutdown(self):
        """Shuts down the service, performing any necessary cleanup."""
