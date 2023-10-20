#!/bin/sh

# run all tests standard way
# pytest tests/ -v

# showing output:
python3 -m pytest tests/ -v -rP

# only one test:
#pytest tests/test_process_metrics.py -v -rP -k test_log
