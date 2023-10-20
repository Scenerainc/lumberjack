"""Module for Azure credentials """
from dataclasses import dataclass
from functools import cached_property

from azure.identity import DefaultAzureCredential


@dataclass
class DefaultCredentials:
    """This class generates shared credentials to be inherited by all Azure services
    that require credentials.
    """

    @cached_property
    def default_credentials(self) -> DefaultAzureCredential:
        """Generate default azure credentials

        Returns:
            DefaultAzureCredential: default azure credentials
        """
        return DefaultAzureCredential()
