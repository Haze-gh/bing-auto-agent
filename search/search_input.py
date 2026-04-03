"""Search input interaction with human-like behavior."""
from playwright.sync_api import Page
import random
from utils.human_behavior import random_delay_before_action


def get_search_input(page: Page):
    """Get search input element with fallback selectors.

    Args:
        page: Playwright page instance

    Returns:
        Locator for search input
    """
    # Try primary selector
    locator = page.locator("input[name='q']")
    if locator.is_visible():
        return locator

    # Try secondary selector
    locator = page.locator("#sb_form_q")
    if locator.is_visible():
        return locator

    # Try placeholder text
    locator = page.get_by_placeholder("Search")
    if locator.is_visible():
        return locator

    raise RuntimeError("Could not find search input element")


def type_search_query(page: Page, query: str) -> None:
    """Type search query with human-like delays.

    Args:
        page: Playwright page instance
        query: Search query string
    """
    search_input = get_search_input(page)

    # Random delay before typing
    random_delay_before_action()

    # Clear and type
    search_input.click()
    search_input.fill("")
    search_input.type(query, delay=random.randint(50, 150))


def submit_search(page: Page) -> None:
    """Submit search by pressing Enter.

    Args:
        page: Playwright page instance
    """
    page.keyboard.press("Enter")


def verify_search_success(page: Page) -> bool:
    """Verify search results page loaded successfully.

    Args:
        page: Playwright page instance

    Returns:
        True if search was successful, False otherwise
    """
    # Check URL contains search parameter
    if config.SEARCH_URL_PARAM in page.url:
        return True

    # Alternative: check for result elements
    try:
        page.wait_for_selector(".b_algo", timeout=5000)
        return True
    except Exception:
        return False


# Need to import config at module level
import config
