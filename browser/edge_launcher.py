"""Edge browser launcher with anti-detection measures."""
from typing import Optional, Union
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext


def get_profile_path_from_config() -> Optional[str]:
    """Get profile path from config, supporting both full path and profile name."""
    import config
    import os

    # If EDGE_PROFILE_PATH is explicitly set to a full path, use it
    if config.EDGE_PROFILE_PATH:
        if os.path.exists(config.EDGE_PROFILE_PATH):
            return config.EDGE_PROFILE_PATH
        return None

    # If EDGE_PROFILE_NAME is set, construct path from base + name
    profile_name = getattr(config, 'EDGE_PROFILE_NAME', None)
    profile_base = getattr(config, 'EDGE_PROFILE_BASE', None)

    if profile_name and profile_base:
        full_path = os.path.join(profile_base, profile_name)
        if os.path.exists(full_path):
            return full_path

    return None


def launch_edge_browser(
    p: Playwright,
    headless: bool = False,
    profile_path: Optional[str] = None
) -> Union[Browser, tuple]:
    """Launch Microsoft Edge browser with anti-detection configuration.

    Args:
        p: Playwright instance
        headless: Whether to run in headless mode
        profile_path: Optional Edge profile path (e.g., '~/.config/microsoft-edge/Default')
                     If provided, uses launch_persistent_context instead.

    Returns:
        Browser instance, or tuple of (Browser, BrowserContext) if profile_path provided
    """
    args = [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--start-maximized',
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-infobars',
        '--disable-extensions',
    ]

    if profile_path:
        # Use persistent context with profile
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=profile_path,
                headless=headless,
                channel='msedge',
                args=args
            )
            return context.browser, context
        except Exception as e:
            print(f"Profile in use or failed to load, falling back to regular launch: {e}")
            # Fall through to regular browser launch

    # Try Edge first, fall back to chromium
    try:
        browser = p.chromium.launch(
            headless=headless,
            channel='msedge',
            args=args
        )
    except Exception:
        browser = p.chromium.launch(
            headless=headless,
            args=args
        )
    return browser
