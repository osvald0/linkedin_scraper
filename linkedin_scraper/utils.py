import logging
import time
from functools import wraps


def setup_logging():
    """
    Configures logging for the scraper.
    Returns configured logger instance.
    """
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)


def retry_on_failure(max_retries=3, delay=1):
    """
    Decorator that retries failed function calls.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        Wrapped function that implements retry logic
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay * (attempt + 1))
            return None

        return wrapper

    return decorator
