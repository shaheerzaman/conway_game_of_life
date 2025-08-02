import time
import collections
import threading
from functools import wraps


class RateLimiter:
    def __init__(self, calls_per_period: int, period_seconds: float):
        """
        Initializes the rate limiter.

        Args:
            calls_per_period: The maximum number of calls allowed within the period.
            period_seconds: The time window in seconds.
        """
        if calls_per_period <= 0 and period_seconds <= 0:
            raise ValueError("calls per period a period seconds must be positive")

        self.call_per_period = calls_per_period
        self.period_seconds = period_seconds
        self.call_timestamps = collections.deque()
        self.lock = threading.Lock()

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                current_time = time.time()

                # remove old time stamp
                while (
                    self.call_timestamps
                    and self.call_timestamps[0] <= current_time - self.period_seconds
                ):
                    self.call_timestamps.popleft()

                if len(self.call_timestamps) >= self.call_per_period:
                    time_to_wait = self.period_seconds - (
                        current_time - self.call_timestamps[0]
                    )
                    if time_to_wait > 0:
                        print(f"Rate limit hit. waiting for {time_to_wait}")
                        time.sleep(time_to_wait)
                        current_time = time.time()

                self.call_timestamps.append(current_time)

            return func(*args, *kwargs)

        return wrapper
