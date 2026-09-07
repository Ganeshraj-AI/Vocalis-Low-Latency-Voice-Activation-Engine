import time
import os
import psutil


class MetricsMonitor:
    """
    Lightweight performance monitor tracking latency, CPU, and memory utilization.
    """

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        # Prime psutil cpu_percent for accurate subsequent readings
        self.process.cpu_percent(interval=None)

    def measure_latency(self, func, *args, **kwargs):
        """
        Executes a function, measures its execution time in milliseconds,
        and returns both the function's return value and the elapsed latency.

        Returns:
            tuple: (result of func, latency_in_ms)
        """
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        latency_ms = (end_time - start_time) * 1000.0
        return result, latency_ms

    def get_system_metrics(self) -> dict:
        """
        Gathers current CPU utilization (%) and Memory RSS usage (MB).

        Returns:
            dict: Containing 'cpu_percent' (float) and 'memory_mb' (float).
        """
        # Process CPU utilization since last call
        cpu_percent = self.process.cpu_percent(interval=None)
        
        # Resident Set Size (RSS) memory converted to Megabytes
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / (1024.0 * 1024.0)

        return {
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb
        }
