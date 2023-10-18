"""Unit tests for the process metrics logging module.

Example Usage
-------------

From CMD, navigate into the lumberjack directory and execute:
    python -m pytest tests/unit/test_process_metrics.py -v
"""
from datetime import datetime
import json
from unittest.mock import Mock, ANY
import pytest

from metrics_config import ProcessMetricsConfig
from process_metrics import ProcessMetrics, MetricsLogger, ProcessMetricsEncoder
from azure.monitor.ingestion import UploadLogsStatus, UploadLogsResult, LogsIngestionClient

config = ProcessMetricsConfig()

@pytest.fixture(scope="function")
def metrics_logger() -> MetricsLogger:
    """MetricsLogger fixture

    Returns:
        MetricsLogger: MetricsLogger instance

    Yields:
        Iterator[MetricsLogger]: MetricsLogger instance
    """
    return MetricsLogger()

class Test_MetricsLogger:
    def test_init_creates_class_obj(self, metrics_logger: MetricsLogger):
        # Arrange
        empty_metrics_obj = ProcessMetrics()

        # Act
        # Using fixture so nothing to do here

        # Assert
        assert metrics_logger.metrics == empty_metrics_obj
        assert metrics_logger.rule_id == config.rule_id
        assert metrics_logger.endpoint == config.endpoint
        assert metrics_logger.stream_name == config.stream_name

        assert metrics_logger.default_credentials is not None
        assert metrics_logger.log_client is not None

    def test_setup_metrics(self, metrics_logger: MetricsLogger):
        # Arrange
        test_process_name = "task-<pipeline>#<process_desc>"

        # Act
        metrics_logger.setup_metrics(test_process_name)

        # Assert
        assert metrics_logger.metrics.process_name == test_process_name
        assert metrics_logger.metrics.execution_id is not None
        assert metrics_logger.metrics.start_time is not None

    def test_complete_metrics(self, metrics_logger: MetricsLogger):
        # Arrange
        test_status = "SUCCESS"
        test_mlflow_url = "azureml://jobs/<job-id>/outputs/artifacts/<path>"

        # Act
        metrics_logger.complete_metrics(test_status, test_mlflow_url)

        # Assert
        assert metrics_logger.metrics.status == test_status
        assert metrics_logger.metrics.mlflow_url == test_mlflow_url
        assert datetime.fromisoformat(metrics_logger.metrics.end_time) is not None

    def test_process_metrics_encoder(self, metrics_logger: MetricsLogger):
        # Arrange
        # Expected metrics schema, not reflective of real log
        expected_metrics_schema = {
            'TimeGenerated': None,
            'ProcessName': None,
            'ExecutionId': None,
            'Environment': 'DEV',
            'Status': 'IN PROGRESS',
            'StartTime': None,
            'EndTime': None,
            'ErrorMessage': [],
            'MlflowUrl': None,
            'ExecutionDetails': {}
        }

        # Act
        encoded_metrics = json.dumps(metrics_logger.metrics, indent=4, cls=ProcessMetricsEncoder)
        metrics_logs = json.loads(encoded_metrics)

        # Assert
        assert metrics_logs == expected_metrics_schema

    def test_log(self, metrics_logger: MetricsLogger, monkeypatch):
        # Arrange
        mock_upload = Mock()
        mock_upload.return_value = UploadLogsResult(failed_logs=[], status=UploadLogsStatus.SUCCESS)

        monkeypatch.setattr(LogsIngestionClient, "upload", mock_upload)

        # Expected metrics schema, not reflective of real log
        expected_metrics_schema = [
            {
                'TimeGenerated': 'test_time',
                'ProcessName': None,
                'ExecutionId': None,
                'Environment': 'DEV',
                'Status': 'IN PROGRESS',
                'StartTime': None,
                'EndTime': None,
                'ErrorMessage': [],
                'MlflowUrl': None,
                'ExecutionDetails': {}
            }
        ]

        # Act
        result: UploadLogsResult = metrics_logger.log()
        
        # Assert
        assert result.status == UploadLogsStatus.SUCCESS
        mock_upload.assert_called_once_with(
            rule_id=metrics_logger.rule_id,
            stream_name=metrics_logger.stream_name,
            logs=ANY
        )

    def test_log_error(self, metrics_logger: MetricsLogger, monkeypatch):
        # Arrange
        test_error = "test error"

        mock_log = Mock()
        mock_log.return_value = UploadLogsResult(failed_logs=[], status=UploadLogsStatus.SUCCESS)

        monkeypatch.setattr(MetricsLogger, "log", mock_log)

        # Act
        result = metrics_logger.log_error(test_error)
        
        # Assert
        assert test_error in metrics_logger.metrics.error_message
        assert result.status == UploadLogsStatus.SUCCESS
        mock_log.assert_called_once()
