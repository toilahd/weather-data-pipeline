"""
Performance monitoring and metrics collection
"""
import time
import functools
from typing import Callable, Any
from .logger_config import setup_logger

logger = setup_logger(__name__)


class PerformanceMonitor:
    """Monitor and track pipeline performance metrics"""
    
    def __init__(self):
        self.metrics = {
            'api_calls': 0,
            'api_failures': 0,
            'api_total_time': 0,
            'db_inserts': 0,
            'db_failures': 0,
            'db_total_time': 0,
            'validation_failures': 0
        }
    
    def record_api_call(self, success: bool, duration: float):
        """Record API call metrics"""
        self.metrics['api_calls'] += 1
        self.metrics['api_total_time'] += duration
        if not success:
            self.metrics['api_failures'] += 1
    
    def record_db_insert(self, success: bool, duration: float):
        """Record database insert metrics"""
        self.metrics['db_inserts'] += 1
        self.metrics['db_total_time'] += duration
        if not success:
            self.metrics['db_failures'] += 1
    
    def record_validation_failure(self):
        """Record validation failure"""
        self.metrics['validation_failures'] += 1
    
    def get_summary(self) -> dict:
        """Get performance summary"""
        summary = {
            'api': {
                'total_calls': self.metrics['api_calls'],
                'failures': self.metrics['api_failures'],
                'success_rate': self._calculate_rate(
                    self.metrics['api_calls'] - self.metrics['api_failures'],
                    self.metrics['api_calls']
                ),
                'avg_duration': self._calculate_avg(
                    self.metrics['api_total_time'],
                    self.metrics['api_calls']
                )
            },
            'database': {
                'total_inserts': self.metrics['db_inserts'],
                'failures': self.metrics['db_failures'],
                'success_rate': self._calculate_rate(
                    self.metrics['db_inserts'] - self.metrics['db_failures'],
                    self.metrics['db_inserts']
                ),
                'avg_duration': self._calculate_avg(
                    self.metrics['db_total_time'],
                    self.metrics['db_inserts']
                )
            },
            'validation': {
                'failures': self.metrics['validation_failures']
            }
        }
        return summary
    
    @staticmethod
    def _calculate_rate(success: int, total: int) -> float:
        """Calculate success rate percentage"""
        if total == 0:
            return 0.0
        return round((success / total) * 100, 2)
    
    @staticmethod
    def _calculate_avg(total_time: float, count: int) -> float:
        """Calculate average duration"""
        if count == 0:
            return 0.0
        return round(total_time / count, 3)
    
    def log_summary(self):
        """Log performance summary"""
        summary = self.get_summary()
        logger.info("=" * 60)
        logger.info("Performance Metrics Summary")
        logger.info("-" * 60)
        logger.info(f"API Calls: {summary['api']['total_calls']} "
                   f"(Success Rate: {summary['api']['success_rate']}%)")
        logger.info(f"API Avg Duration: {summary['api']['avg_duration']}s")
        logger.info(f"DB Inserts: {summary['database']['total_inserts']} "
                   f"(Success Rate: {summary['database']['success_rate']}%)")
        logger.info(f"DB Avg Duration: {summary['database']['avg_duration']}s")
        logger.info(f"Validation Failures: {summary['validation']['failures']}")
        logger.info("=" * 60)


def measure_time(metric_name: str = None):
    """Decorator to measure function execution time"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                name = metric_name or func.__name__
                logger.debug(f"{name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                name = metric_name or func.__name__
                logger.error(f"{name} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator
