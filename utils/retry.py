"""Retry decorator for handling transient failures."""
import time
import functools
import config


def retry(timeout: int = None, interval: int = None):
    """Decorator to retry a function on failure.

    Args:
        timeout: Maximum time to retry in seconds (default from config)
        interval: Time between retries in seconds (default from config)

    Returns:
        Decorated function with retry logic
    """
    if timeout is None:
        timeout = config.RETRY_TIMEOUT
    if interval is None:
        interval = config.RETRY_INTERVAL

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            last_exception = None

            while time.time() - start_time < timeout:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if time.time() - start_time < timeout:
                        time.sleep(interval)

            raise last_exception

        return wrapper
    return decorator
