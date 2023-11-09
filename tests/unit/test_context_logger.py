"""ContextLogger Tests"""

import unittest
from unittest.mock import Mock

# pylint: disable=E0401
from lumberjack import MetricsLogger
from lumberjack.utils.context_manager import ContextLogger
# pylint: enable=E0401


class _Exception(BaseException):
    """Test Exception"""


class TestMetricLoggerCM(unittest.TestCase):
    """Context manager tests"""

    def setUp(self):
        """Mock setup"""
        self.mock_endpoint = Mock()
        self.metrics_logger = MetricsLogger()
        self.metrics_logger.log = self.mock_endpoint

    def test_raises(self):
        """Ensure it doesn't suppress exceptions per default"""
        with self.assertRaises(_Exception):
            with ContextLogger(self.metrics_logger, "test"):
                raise _Exception()
        self.mock_endpoint.assert_called()

    def test_not_raises(self):
        """Test optional parameter 'suppress'"""
        with ContextLogger(self.metrics_logger, "test", suppress=True):
            raise _Exception()
        self.mock_endpoint.assert_called()

    def test_yielded_instance(self):
        """Check if the yielded instance is the same as the one it was obtained from"""
        with self.metrics_logger.context("test") as yielded_metrics_logger:
            self.assertEqual(self.metrics_logger, yielded_metrics_logger)
        self.mock_endpoint.assert_called()
