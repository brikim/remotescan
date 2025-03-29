
from logging import Logger
from apscheduler.schedulers.blocking import BlockingScheduler


class ServiceBase:
    """
    Base class for services in the application.

    Provides common logging functionality and a basic interface for
    initializing and shutting down services.
    """

    def __init__(
        self,
        logger: Logger,
        scheduler: BlockingScheduler,
    ):
        """Initializes the ServiceBase with a logger and scheduler."""
        self.logger = logger
        self.scheduler = scheduler

    def _log_info(self, message: str):
        self.logger.info(message)

    def _log_warning(self, message: str):
        self.logger.warning(message)

    def _log_error(self, message: str):
        self.logger.error(message)

    def init_scheduler_jobs(self):
        """Initializes any scheduler jobs for the service."""

    def shutdown(self):
        """Shuts down the service, performing any necessary cleanup."""
