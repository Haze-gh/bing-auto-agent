"""Human behavior simulation for anti-detection."""
import random
import time
import config


def random_delay_before_action(min_ms: int | None = None, max_ms: int | None = None) -> None:
    """Add random delay before performing an action.

    Args:
        min_ms: Minimum delay in ms (default: config.MIN_DELAY_MS)
        max_ms: Maximum delay in ms (default: config.MAX_DELAY_MS)
    """
    if min_ms is None:
        min_ms = config.MIN_DELAY_MS
    if max_ms is None:
        max_ms = config.MAX_DELAY_MS
    delay = random.randint(min_ms, max_ms)
    time.sleep(delay / 1000.0)


def random_keyboard_delay() -> int:
    """Get random delay between keystrokes in milliseconds.

    Returns:
        Random delay in ms between MIN_KEYSTROKE_DELAY and MAX_KEYSTROKE_DELAY
    """
    return random.randint(config.MIN_KEYSTROKE_DELAY_MS, config.MAX_KEYSTROKE_DELAY_MS)
