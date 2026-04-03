"""Human behavior simulation for anti-detection."""
import random
import time
import config


def random_delay_before_action() -> None:
    """Add random delay before performing an action."""
    delay = random.randint(config.MIN_DELAY_MS, config.MAX_DELAY_MS)
    time.sleep(delay / 1000.0)


def random_keyboard_delay() -> int:
    """Get random delay between keystrokes in milliseconds.

    Returns:
        Random delay in ms between MIN_KEYSTROKE_DELAY and MAX_KEYSTROKE_DELAY
    """
    return random.randint(config.MIN_KEYSTROKE_DELAY_MS, config.MAX_KEYSTROKE_DELAY_MS)
