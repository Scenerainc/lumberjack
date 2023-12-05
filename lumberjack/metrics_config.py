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

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient
import json


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

    def __init__(self):
        storage_account_name = "stscenera002devtf"
        container_name = "default"
        blob_name = "layer1"
        account_url = f"https://{storage_account_name}.blob.core.windows.net"
        default_credential = DefaultAzureCredential()

        blob_service_client = BlobServiceClient(account_url, credential=default_credential)
        self.blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)


    @cached_property
    def environment(self) -> str:
        """Generate environment variable.

        Returns:
            string : application environment DEV, TEST, PROD
        """
        return os.getenv("app", "DEV")

    @cached_property
    def rule_id(self) -> str:
        """Generate Azure data collection rule immutable ID.

        Returns:
            string : Azure data collection rule immutable ID

        Example:
            "dcr-abc123"

        """
        output_key = "data_collection_rule_immutable_id"
        return get_terraform_output_from_remote_state(self.blob_client, output_key)

    @cached_property
    def endpoint(self) -> str:
        """Generate Azure data collection endpoint.

        Returns:
            string : Azure data collection endpoint

        Example:
            "https://<unique-dce-identifier>.<regionname>-1.ingest.monitor.azure.com"
        """
        output_key = "data_collection_endpoint_logs_ingestion_endpoint"
        return get_terraform_output_from_remote_state(self.blob_client, output_key)

    @cached_property
    def stream_name(self) -> str:
        """Generate Azure data collection rule stream name.

        Returns:
            string : Azure data collection rule stream name
        """
        output_key = "data_collection_rule_output_stream"
        return get_terraform_output_from_remote_state(self.blob_client, output_key)


# Should this take self or a blob client as the first param?
def get_terraform_output_from_remote_state(blob_client, output_key):
    try:
        # Download and parse the Terraform state
        state_content = blob_client.download_blob().readall().decode("utf-8")
        state_data = json.loads(state_content)

        # Extract the value of the specified output key
        output_value = state_data.get('outputs', {}).get(output_key, {}).get('value')

        return output_value
    except Exception as e:
        print(f"Error querying remote Terraform state: {e}")
        raise

