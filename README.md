<!-- omit in toc -->
# lumberjack 🪵🪓

Azure Log Analytics logging helper library

- [Key Features](#key-features)
- [How To Use](#how-to-use)
  - [Prerequisites](#prerequisites)
  - [Authentication](#authentication)
  - [Run the sample](#run-the-sample)
- [Packaging and Distribution](#packaging-and-distribution)
- [Helpful Links](#helpful-links)

## Key Features

- Object oriented custom log object
  - Easily craft and update log object using Python's `@dataclass` and dot syntax
- Logger controller
  - Maintains Azure Log Analytics `LogsIngestionClient` with automatic configuration and authentication using credentials
  - Easily reusable logging functions
  - Handles datetime formatting (TODO)
- JSON Encoder
  - Easily transition log object from python object format to Log Analytics custom table schema format

## How To Use

### Prerequisites

1. Log Analytics workspace
1. [Log Analytics custom table (DCR-Based)](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/tutorial-logs-ingestion-portal#create-new-table-in-log-analytics-workspace)
    - **_Using Azure Portal:_**
        - When creating the Log Analytics custom table in the portal, select the `New custom log (DCR-based)` option. Under Data Collection Rule choose "Create a new data collection rule". This way, the newly created Data Collection Rule is automatically linked with the Custom Table. Creating a Data Collection Rule independently through Azure Monitor for use with a custom table is not advised.
        - After completing the Basics step, you will be prompted to "Upload sample of logs in JSON format" where you can use the [`sample_log_schema.json`](./lumberjack/sample_log_schema.json) provided

        > **_NOTE:_** All fields in sample JSON format must follow PascalCase

    - **_Using Terraform:_**
        - The Data Collection Rule and Log Analytics custom table can be independently created, linked, and managed using `azurerm` provider. This will also configure the custom log schema.
2. [Data Collection Endpoint](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/tutorial-logs-ingestion-portal#create-data-collection-endpoint)
3. [Assign **Monitoring Metrics Publisher** permissions to the Data Collection Rule](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/tutorial-logs-ingestion-portal#assign-permissions-to-the-dcr)
    - This permission can be granted to a user (local testing) or a service principle (running live)
    > **_NOTE_** A newly granted permission can take ~10 mins to take effect.
4. Setup Env Variables (currently hardcoded in [`config.py`](./lumberjack/metrics_config.py))
    - `rule_id`= [The `immutableId` of the Data Collection Rule](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/tutorial-logs-ingestion-portal#collect-information-from-the-dcr)
    - `endpoint`= [Logs ingestion URI from the Data Collection Endpoint](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/tutorial-logs-ingestion-portal#create-data-collection-endpoint)
    - `stream_name`= "`Custom-<custom_table_name>`" (must begin with `Custom-` as per [Structure of a data collection rule in Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/data-collection-rule-structure#streamdeclarations))

### Authentication

This sample uses a call to Azure Identity's `DefaultAzureCredential()` to authenticate the caller. In "live" running services, this should be a Service Principle. In a local run, simply run:

```bash
az login
```

Next verify the currently set account:

```bash
az account show
```

If you need to change subscription:

```bash
az account set --subscription <name or id>
```

### Run the sample

```bash
$ pip install -r requirements.txt
$ cd lumberjack
$ python3 sample_log_activity.py
>>> status:Success
```

Navigate to Log Analytics Workspace > Logs and query your custom table for the newly added logs.

## Packaging and Distribution

TODO

## Helpful Links

[Tutorial: Send data to Azure Monitor Logs with Logs ingestion API (Azure portal)](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/tutorial-logs-ingestion-portal)
