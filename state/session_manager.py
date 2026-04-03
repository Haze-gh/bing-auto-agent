"""State persistence for browser session."""
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext
import config
import os


def create_context_with_state(browser: Browser) -> BrowserContext:
    """Create browser context, loading existing state if available.

    Args:
        browser: Playwright browser instance

    Returns:
        BrowserContext with state loaded if available
    """
    if os.path.exists(config.STATE_FILE):
        try:
            context = browser.new_context(storage_state=config.STATE_FILE)
            print(f"Loaded state from {config.STATE_FILE}")
            return context
        except Exception as e:
            print(f"Failed to load state: {e}, creating fresh context")
            return browser.new_context()
    else:
        return browser.new_context()


def save_state(context: BrowserContext) -> None:
    """Save browser context state to file.

    Args:
        context: Playwright browser context
    """
    context.storage_state(path=config.STATE_FILE)
    print(f"State saved to {config.STATE_FILE}")
