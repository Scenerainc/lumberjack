"""Module for logging process metrics In Log Analytics."""
from dataclasses import dataclass, field
import json
from json import JSONEncoder
import string
from typing import List, Optional
from datetime import datetime

from azure.core.exceptions import HttpResponseError
from azure.monitor.ingestion import LogsIngestionClient, UploadLogsStatus, UploadLogsResult

from credentials import DefaultCredentials
from metrics_config import ProcessMetricsConfig

config = ProcessMetricsConfig()

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
    # TODO: use literals for env and status strings?
    environment: str = config.environment
    status: str = "IN PROGRESS"
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
        # pylint: disable-next=C0301
        encoded_metrics = {string.capwords(k.replace("_", " ")).replace(" ", ""):v for k,v in o.__dict__.items()}
        return encoded_metrics


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

    def setup_metrics(self, process_name: str) -> None:
        """Initialize metrics object at the start of a process.

        Args:
            process_name (str): process name typically in the form of: task-<pipeline>#<process_desc>

        Returns:
            None
        """
        # TODO: helpers and validation functions for time
        start_time = datetime.utcnow().isoformat()
        self.metrics.process_name = process_name
        self.metrics.execution_id = f"{process_name}@{start_time}" # this will be a unique ID
        self.metrics.start_time = start_time
        
    def complete_metrics(self, status: str, mlflow_url: str) -> None:
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
        # TODO: Check if this gets populated automatically? Or can it (possibly via use of Transformations)
        self.metrics.time_generated = datetime.utcnow().isoformat()

        encoded_metrics = json.dumps(self.metrics, indent=4, cls=ProcessMetricsEncoder)
        metrics_logs = [json.loads(encoded_metrics)]

        try:
            response = self.log_client.upload(
                rule_id=self.rule_id, stream_name=self.stream_name, logs=metrics_logs)

            if response.status != UploadLogsStatus.SUCCESS:
                failed_logs = response.failed_logs
                print(failed_logs)
            else:
                # TODO: Let's revisit this, it always prints status:Success and is not very informative
                # It is not necessarily a confirmation that the log landed in the table
                # Just that the server accepted the request 
                print(f"status:{response.status}")

            return response
        except HttpResponseError as err:
            print(f"Unable to upload the metrics: {err}")
        except KeyError as key:
            # Is this possible if the metrics object is always created in the same way
            raise KeyError(f"{key} is missing") from key
        except Exception as ex:
            raise Exception(f"Unexpected Error : {ex}") from ex

    def log_error(self, error) -> UploadLogsResult:
        """Build error message and call log().

        Args:
            error (string): error message to append to metrics object

        Returns:
            UploadLogsResult: The response for send_logs API.
        """
        self.metrics.error_message.append(f"{error}")
        return self.log()
