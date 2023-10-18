import os
from time import sleep
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)

from process_metrics import MetricsLogger

metrics_logger = MetricsLogger()
metrics_logger.setup_metrics(process_name="Sample Process")

# DO SOMETHING 

metrics_logger.complete_metrics(status="SUCCESS", mlflow_url="azureml://jobs/<job-id>/outputs/artifacts/<path>")
response = metrics_logger.log()
