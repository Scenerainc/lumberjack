"""Context Manager approach for using the MetricsLogger"""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    # Removing the check will result in circular exports
    # all this is only used for type annotations
    import threading, multiprocessing, asyncio  # pylint: disable=C0410
    from types import TracebackType
    from typing import Union, Optional
    from lumberjack import MetricsLogger

    _LockType = Union[threading.Lock, multiprocessing.Lock, asyncio.Lock]


class ContextLogger(AbstractContextManager):
    """Context Logger"""

    logger: "MetricsLogger"
    process_name: str

    mlflow_url: "Optional[str]"
    suppress: bool
    __lock: "Optional[_LockType]"

    def __init__(
        # pylint: disable=R0913
        # Disabled 'too-many-arguments',
        # only 2 of them are required positional arguments
        # the rest is optional
        self,
        metrics_logger: "MetricsLogger",
        process_name: str,
        mlflow_url: str = None,
        suppress: bool = False,
        lock: "Optional[_LockType]" = None,
    ):
        """Context Logger

        Though one can suppress exceptions in the with block with the suppress key-word argument,
        this is not intended to replace error handling

        Args:
            metrics_logger (MetricsLogger): \
                Metrics logger 'parent' class
            process_name (str): \
                process name typically in the form of: task-<pipeline>#<process_desc>
            mlflow_url (str, optional): \
                url location of the process's MLflow artifacts (logs/metrics/model), by default None
            suppress (bool, optional): \
                suppress exceptions, by default False (use responsibly)
            lock : (Lock, optional): \
                Optional lock for thread safety, by default None
        """
        self.logger = metrics_logger
        self.process_name = process_name
        self.mlflow_url = mlflow_url
        self.suppress = suppress
        self.__lock = lock

    def __enter__(self) -> "MetricsLogger":
        """Enter the context"""
        if self.__lock:
            self.__lock.acquire(blocking=True)
        self.logger.setup_metrics(self.process_name)
        return self.logger

    def __exit__(
        self,
        exc_type: "Optional[BaseException]" = None,
        exc_info: "Optional[BaseException]" = None,
        traceback: "Optional[TracebackType]" = None,
    ) -> bool:
        """Exit the context"""
        status = "SUCCESS"
        exception = any([exc_type, exc_info, traceback])
        if exception:
            status = "FAILURE"
        self.logger.complete_metrics(status=status, mlflow_url=self.mlflow_url)
        if exception:
            self.logger.log_error(exc_info)
        else:
            self.logger.log()
        if self.__lock:
            self.__lock.release()
        return self.suppress
