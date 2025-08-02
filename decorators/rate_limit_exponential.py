import time
import random
from functools import wraps


class Retry:
    def __init__(
        self,
        retries: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions=(Exception,),
        jitter: bool = True,
    ):
        self.retries = retries
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions
        self.jitter = jitter

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _delay = self.delay
            for i in range(self.retries + 1):
                try:
                    return func(*args, **kwargs)
                except self.exceptions as e:
                    if i == self.retries:
                        print(
                            f"Attempt {i + 1}/{self.retries + 1}: Failed after all retries. Raising exception."
                        )
                        raise  # Re-raise the last exception if all retries are exhausted

                    current_delay = _delay
                    if self.jitter:
                        current_delay = current_delay * (1 + random.uniform(-0.1, 0.1))

                    print(
                        f"Attempt {i + 1}/{self.retries + 1}: {e.__class__.__name__} caught. Retrying in {current_delay:.2f} seconds..."
                    )
                    time.sleep(current_delay)
                    _delay *= self.backoff_factor  # increase delay for next attempt

            return func(*args, **kwargs)

        return wrapper


import requests

# Simulate a flaky network call
call_count = 0


@Retry(
    retries=4,
    delay=0.5,
    backoff_factor=2,
    exceptions=(requests.exceptions.ConnectionError, requests.exceptions.Timeout),
    jitter=True,
)
def make_api_call(url):
    global call_count
    call_count += 1
    print(f"Making API call to {url} (Attempt {call_count})...")
    if call_count < 3:  # Simulate failure for the first 2 calls
        raise requests.exceptions.ConnectionError("Simulated network issue")
    elif call_count == 3:  # Simulate success on the 3rd call
        print("API call successful!")
        return {"status": "success", "data": "Hello from API"}
    else:  # Subsequent calls also succeed
        print("API call successful (subsequent).")
        return {"status": "success", "data": "Hello from API"}
