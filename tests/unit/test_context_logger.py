"""ContextLogger Tests"""

import unittest
from unittest.mock import Mock

from lumberjack import MetricsLogger
from lumberjack.process_metrics import ContextLogger


class _Exception(BaseException):
    pass


class TestMetricLoggerCM(unittest.TestCase):
    def test_raises(self):
        # Arrange
        mock = Mock()
        with self.assertRaises(_Exception):
            with ContextLogger("test", suppress=False) as logger:
                setattr(logger, "log", mock)
                raise _Exception()
        mock.assert_called()

    def test_not_raises(self):
        mock = Mock()
        with ContextLogger("test", suppress=True) as logger:
            setattr(logger, "log", mock)
            raise _Exception()
        mock.assert_called()

    def test_static_method(self):
        self.assertIsInstance(MetricsLogger.context("test"), ContextLogger)