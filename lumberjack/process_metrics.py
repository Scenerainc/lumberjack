"""Module for logging process metrics In Log Analytics."""
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import datetime
import json
from json import JSONEncoder
import logging
import string
from types import TracebackType
from typing import Any, List, Literal, Optional

from azure.core.exceptions import HttpResponseError
from azure.monitor.ingestion import LogsIngestionClient, UploadLogsStatus, UploadLogsResult

from lumberjack.credentials import DefaultCredentials
from lumberjack.metrics_config import ProcessMetricsConfig

# Literal string union type for process metrics status
PROCESS_METRIC_STATUS = Literal["IN PROGRESS", "SUCCESS", "FAILURE"]

# Literal string union type for process metrics environment
PROCESS_METRICS_ENV = Literal["DEV", "TEST", "PROD"]

config = ProcessMetricsConfig()
logging.basicConfig(level=logging.INFO)

@dataclass
class ProcessMetrics:
    """Dataclass for process metrics object.

    Based on the MLOpsPipelineLogs_CL custom Log Analytics table schema
    """

    # pylint: disable=too-many-instance-attributes
    # Ten attributes is reasonable and is the schema definition in Log Analytics

    time_generated: Optional[str] = None
    process_name: Optional[str] = None
    execution_id: Optional[str] = None
    environment: PROCESS_METRICS_ENV = config.environment
    status: Optional[PROCESS_METRIC_STATUS] = None
    start_time: Optional[str] = None
    end_time: Optional[str]  = None
    error_message: List[str] = field(default_factory=list)
    mlflow_url: Optional[str] = None 
    execution_details: dict = field(default_factory=dict)


class ProcessMetricsEncoder(JSONEncoder):
    """Class for json encoding ProcessMetrics object.

    JSON Encoder class to convert ProcessMetrics object into the format expected
        in MLOpsPipelineLogs_CL custom Log Analytics table.
        Converts the snake_case keys on the metrics object to PascalCase.
    """

    def default(self, o):
        """Encode object.

        Args:
            o (ProcessMetrics): ProcessMetrics object to be encoded

        Returns:
            encoded_metrics: encoded metrics
        """
        encoded_metrics = {
            string.capwords(k.replace("_", " ")).replace(" ", ""): v
            for k, v in o.__dict__.items()
        }

        return encoded_metrics

class ContextLogger(AbstractContextManager):
    """Context Logger"""
    suppress: bool
    _logger: "MetricsLogger"
    __lock: Any

    def __init__(
            self,
            process_name: str,
            mlflow_url: str = None,
            suppress: bool = False,
            lock: Optional[Any] = None
        ):
        """Context Logger

        Though one can suppress exceptions in the with block with the suppress key-word argument,
        this is not intended to replace error handling

        Args:
            process_name (str): \
                process name typically in the form of: task-<pipeline>#<process_desc>
            mlflow_url (str, optional): \
                url location of the process's MLflow artifacts (logs/metrics/model), by default None
            suppress (bool, optional): \
                suppress exceptions, by default False
            lock : (Lock, optional): \
                Optional lock for thread safety, by default None
        """
        self.process_name = process_name
        self.suppress = suppress
        self.mlflow_url = mlflow_url
        self.__lock = lock
        self._logger = MetricsLogger()

    def __enter__(self) -> "MetricsLogger":
        """Enter the context"""
        if self.__lock:
            self.__lock.acquire(blocking=True)
        self._logger.setup_metrics(self.process_name)
        return self._logger

    def __exit__(
            self,
            exc_type: BaseException = None,
            exc_info: BaseException = None,
            traceback: TracebackType = None,
        ) -> bool:
        """Exit the context"""
        status = "SUCCESS"
        exception = any([exc_type, exc_info, traceback])
        if exception:
            status = "FAILURE"
        self._logger.complete_metrics(status=status, mlflow_url=self.mlflow_url)
        if exception:
            self._logger.log_error(exc_info)
        else:
            self._logger.log()
        if self.__lock:
            self.__lock.release()
        return self.suppress

class MetricsLogger(DefaultCredentials):
    """Class for logging process metrics in Log Analytics.

        Creates and maintains LogIngestionClient instance using rule id, endpoint,
        and stream name provided by config.

    Args:
        DefaultCredentials: Inheriting DefaultAzureCredential

    Methods:
        log(): Upload logs to Log Analytics
        log_error(): Helper method to append error details to ProcessMetrics object and
            then call log()

    """

    def __init__(self):
        """Create a new MetricsLogger object.

        Gets Azure Log Analytics configurations, creates a LogsIngestionClient
        and a blank ProcessMetrics object
        """
        self.metrics = ProcessMetrics()

        # Log Analytics data collection rule details
        self.rule_id = config.rule_id
        self.endpoint = config.endpoint
        self.stream_name = config.stream_name

        self.log_client = LogsIngestionClient(
            endpoint=self.endpoint, credential=self.default_credentials, logging_enable=True)

    @staticmethod
    def context(process_name: str, *context_logger_args, **context_logger_kwargs):
        """Context Logger

        Though one can suppress exceptions in the with block with the suppress key-word argument,
        this is not intended to replace error handling

        Args:
            process_name (str): \
                process name typically in the form of: task-<pipeline>#<process_desc>
            mlflow_url (str, optional): \
                url location of the process's MLflow artifacts (logs/metrics/model), by default None
            suppress (bool, optional): \
                suppress exceptions, by default False
            lock : (Lock, optional): \
                Optional lock for thread safety, by default None

        Example:
        
        >>> from lumberjack import MetricsLogger
        >>> with MetricsLogger.context("run#topic") as metrics_logger:
        >>>     print(metrics_logger.__class__)
        <class 'lumberjack.process_metrics.MetricsLogger'>

        """
        return ContextLogger(process_name, *context_logger_args, **context_logger_kwargs)



    def setup_metrics(self, process_name: str) -> None:
        """Initialize metrics object at the start of a process.

        Args:
            process_name (str): process name typically in the form of: task-<pipeline>#<process_desc>

        Returns:
            None
        """
        start_time = datetime.utcnow().isoformat()
        self.metrics.process_name = process_name
        self.metrics.execution_id = f"{process_name}@{start_time}" # this will be a unique ID
        self.metrics.start_time = start_time
        
    def complete_metrics(self, status: PROCESS_METRIC_STATUS, mlflow_url: str) -> None:
        """Complete metrics object at the end of a process with status and end time.

        Args:
            status(str): The status of the process: "IN PROGRESS", "SUCCESS", "FAILURE"
            mlflow_url(str): url location of the process's MLflow artifacts (logs/metrics/model) 

        Returns:
            None
        """
        self.metrics.status = status
        self.metrics.mlflow_url = mlflow_url
        self.metrics.end_time = datetime.utcnow().isoformat()

    def log(self) -> UploadLogsResult:
        """Prepare log object and upload to Log Analytics.

        Args:
            None, all information is available on the MetricsLogger object

        Returns:
            UploadLogsResult: The response for send_logs API.
        """
        self.metrics.time_generated = datetime.utcnow().isoformat()

        encoded_metrics = json.dumps(self.metrics, indent=4, cls=ProcessMetricsEncoder)
        metrics_logs = [json.loads(encoded_metrics)]

        try:
            response = self.log_client.upload(
                rule_id=self.rule_id, stream_name=self.stream_name, logs=metrics_logs)

            if response.status != UploadLogsStatus.SUCCESS:
                failed_logs = response.failed_logs
                logging.warn(failed_logs)
            else:
                logging.info(f"status:{response.status}")

            return response
        except HttpResponseError as err:
            logging.error(f"Unable to upload the metrics: {err}")
        except Exception as ex:
            logging.error(f"Failed to log, unexpected exception: {ex}")
            raise

    def log_error(self, error) -> UploadLogsResult:
        """Build error message and call log().

        Args:
            error (string): error message to append to metrics object

        Returns:
            UploadLogsResult: The response for send_logs API.
        """
        self.metrics.error_message.append(f"{error}")
        self.metrics.status = "FAILURE"
        return self.log()
