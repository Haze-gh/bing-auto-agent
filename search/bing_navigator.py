"""Bing navigation module."""
import time
from playwright.sync_api import Page
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError
import config


def navigate_to_bing(page: Page, max_retries: int = 3) -> None:
    """Navigate to Bing search engine.

    Args:
        page: Playwright page instance
        max_retries: Number of retry attempts on timeout (default 3)
    """
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            page.goto(config.BING_URL)
            page.wait_for_load_state("networkidle")
            return
        except PlaywrightTimeoutError as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(2)
            continue
    raise last_error


def navigate_with_retry(page: Page, url: str, max_retries: int = 3,
                         timeout: int = 15000) -> None:
    """Navigate to a URL with retry on 404 or timeout.

    Args:
        page: Playwright page instance
        url: Target URL to navigate to
        max_retries: Number of retry attempts (default 3)
        timeout: Page load timeout in ms (default 15000)
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = page.goto(url, timeout=timeout, wait_until="networkidle")
            final_url = page.url
            # Detect 404: HTTP status 404 OR URL contains 404 indicators
            is_404 = (response and response.status == 404) or (
                "404" in final_url or
                final_url == "about:blank" or
                "nf/404" in final_url
            )
            if is_404:
                if attempt < max_retries:
                    print(f"[Navigate] Got 404 for {url} (URL: {final_url}), retrying ({attempt}/{max_retries})...")
                    time.sleep(2)
                    continue
                else:
                    raise Exception(f"HTTP 404 on {url} (final URL: {final_url}) after {max_retries} attempts")
            return
        except PlaywrightTimeoutError:
            if attempt < max_retries:
                print(f"[Navigate] Timeout on {url}, retrying ({attempt}/{max_retries})...")
                time.sleep(2)
                continue
            raise
        except Exception as e:
            if "404" in str(e) and attempt < max_retries:
                time.sleep(2)
                continue
            raise


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
