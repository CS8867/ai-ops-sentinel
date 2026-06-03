```python
from models import MetricInput, HealthReport
from typing import List


def compute_error_rate(metric: MetricInput) -> float:
    """Calculate the error rate for a given service metric.
    
    Guards against ZeroDivisionError when service traffic is zero.
    """
    if metric.total_requests == 0:
        return 0.0
        
    error_rate = metric.failed_requests / metric.total_requests
    return round(error_rate, 4)


def classify_health(error_rate: float, latency_ms: float) -> str:
    """Classify service health based on error rate and latency thresholds."""
    if error_rate > 0.05:
        return "CRITICAL"
    elif error_rate > 0.01 or latency_ms > 500:
        return "DEGRADED"
    return "HEALTHY"
```