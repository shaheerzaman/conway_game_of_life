import time
from functools import wraps
import threading


class CacheWithTTL:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.lock = threading.Lock()

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, frozenset(kwargs.items()))
            with self.lock:
                if key in self.cache:
                    result, timestamp = self.cache[key]
                    if time.time() - timestamp < self.ttl_seconds:
                        return result
                    else:
                        self.cache.pop()

                print(f"cache miss for {func.__name__} with key {key}")
                result = func(*args, **kwargs)
                self.cache[key] = (result, time.time())
                return result

        wrapper.cache_clear = self.clear_cache
        wrapper.cache_invalidate = lambda *args, **kwargs: self.invaildate_key(
            *args, **kwargs
        )
        return wrapper

    def clear_cache(self):
        with self.lock:
            self.cache.clear()

    def invalidate_key(self, args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        with self.lock:
            if key in self.cache:
                print(f"Invalidating cache for key {key}")
                self.cache.pop(key)
            else:
                print(f"key {key} not found in cache")


@CacheWithTTL(ttl_seconds=10)  # Cache results for 10 seconds
def get_user_data(user_id, fetch_details=False):
    """Simulates a slow database query."""
    print(
        f"--- Fetching user data for {user_id} (details: {fetch_details})... (simulating 2s delay)"
    )
    time.sleep(2)  # Simulate network/DB latency
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "details": "..." if fetch_details else "summary",
    }


print("--- Initial calls ---")
print(get_user_data(1))
print(get_user_data(2, fetch_details=True))
print(get_user_data(1))  # Should be a cache hit

print("\n--- Waiting 5 seconds (still cached) ---")
time.sleep(5)
print(get_user_data(1))  # Should still be a cache hit

print("\n--- Waiting another 6 seconds (cache expired) ---")
time.sleep(6)  # Total 11 seconds elapsed
print(get_user_data(1))  # Should re-compute

print("\n--- Testing manual invalidation ---")
print(get_user_data(3))  # New call, will compute and cache
print(get_user_data(3))  # Cache hit

print("Clearing cache for get_user_data...")
get_user_data.cache_clear()  # Call the added method

print(get_user_data(3))  # Should re-compute after clear

print("\n--- Testing specific key invalidation ---")
print(get_user_data(4, fetch_details=True))  # Compute and cache
print(get_user_data(4, fetch_details=True))  # Cache hit

print("Invalidating cache for user 4 with details=True...")
get_user_data.cache_invalidate(4, fetch_details=True)

print(get_user_data(4, fetch_details=True))  # Should re-compute

print("\n--- Done ---")
