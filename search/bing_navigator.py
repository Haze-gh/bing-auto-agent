"""Bing navigation module."""
from playwright.sync_api import Page
import config


def navigate_to_bing(page: Page) -> None:
    """Navigate to Bing search engine.

    Args:
        page: Playwright page instance
    """
    page.goto(config.BING_URL)
    page.wait_for_load_state("networkidle")


def verify_bing_loaded(page: Page) -> bool:
    """Verify Bing search box is visible.

    Args:
        page: Playwright page instance

    Returns:
        True if search box is visible, False otherwise
    """
    # Try primary selector
    search_box = page.locator("input[name='q']")
    if search_box.is_visible():
        return True

    # Try secondary selector
    search_box = page.locator("#sb_form_q")
    if search_box.is_visible():
        return True

    return False
