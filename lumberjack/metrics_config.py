"""
This module contains the definition of configuration class for ProcessMetricsConfig.

Classes:
    ProcessMetricsConfig: A class that does operations on formatting ProcessMetricsConfig.

Usage:
    To use the ProcessMetricsConfig class, create an instance and call its methods.

Example:
    
"""
from dataclasses import dataclass
from functools import cached_property
import os


@dataclass
class ProcessMetricsConfig:
    """
    Configuration require for Process Metrics class.

    cached_property:
        environment(): application environment
        rule_id(): Azure data collection rule ID
        endpoint(): Azure data collection endpoint
        stream_name(): Azure data collection rule stream name
    """

    @cached_property
    def environment(self) -> str:
        """Generate environment variable.

        Returns:
            string : application environment DEV, TEST, PROD
        """
        return os.getenv("app", "DEV")

    @cached_property
    def rule_id(self) -> str:
        """Generate Azure data collection rule ID.

        Returns:
            string : Azure data collection rule ID
        """
        return "dcr-c03b5871ae9b4f75a3486db8796cc6e1"

    @cached_property
    def endpoint(self) -> str:
        """Generate Azure data collection endpoint.

        Returns:
            string : Azure data collection endpoint
        """
        return "https://dce-mlops-pipeline-t02o.koreacentral-1.ingest.monitor.azure.com"

    @cached_property
    def stream_name(self) -> str:
        """Generate Azure data collection rule stream name.

        Returns:
            string : Azure data collection rule stream name
        """
        return "Custom-MLOpsPipelineLogs_CL"
