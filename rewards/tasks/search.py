"""Daily Bing search task for Microsoft Rewards."""
from __future__ import annotations

import json
import os
import random
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

import config
from search.bing_navigator import navigate_with_retry
from utils.human_behavior import random_delay_before_action


# Points earned per search
POINTS_PER_SEARCH = 3

# Cache for loaded search terms
_SEARCH_TERMS_CACHE = None


def _close_extra_tabs(page: Page) -> int:
    """Close all tabs except Bing search pages.

    Args:
        page: Playwright page instance

    Returns:
        Number of tabs closed
    """
    closed_count = 0
    context = page.context

    try:
        for tab in context.pages:
            if tab == page:
                continue

            tab_url = tab.url.lower()
            is_bing_search = (
                'bing.com/search' in tab_url or
                'cn.bing.com' in tab_url
            )

            if not is_bing_search:
                tab.close()
                closed_count += 1
                print(f"[Tab Cleanup] Closed non-search tab: {tab_url[:60]}")

        if closed_count > 0:
            print(f"[Tab Cleanup] Closed {closed_count} extra tab(s)")
            page.wait_for_timeout(500)

    except Exception as e:
        print(f"[Tab Cleanup] Error closing tabs: {e}")

    return closed_count


def _get_search_input_on_current_page(page: Page):
    """Find search input on the current page without navigating.

    Args:
        page: Playwright page instance

    Returns:
        Locator for the search input

    Raises:
        RuntimeError: If search input cannot be found
    """
    selectors = [
        "input[name='q']",
        "#sb_form_q",
        "input[placeholder='Search']",
        "[aria-label='Search input']",
    ]

    for selector in selectors:
        search_input = page.locator(selector)
        if search_input.is_visible():
            return search_input

    raise RuntimeError("Search input not found on current page")


def _try_random_pagination(page: Page) -> bool:
    """Attempt to click a random pagination button during wait time.

    Args:
        page: Playwright page instance

    Returns:
        True if pagination was clicked, False otherwise
    """
    pagination_selectors = [
        "a[aria-label='Page 2']",
        "a[aria-label='Page 3']",
        "a[aria-label='Page 4']",
        "a[aria-label='Page 5']",
        "li[class*='b_pag'] a",
        "#b_pagination a",
        ".pagination a",
    ]

    visible_pages = []
    for selector in pagination_selectors:
        elements = page.locator(selector)
        count = elements.count()
        for i in range(count):
            el = elements.nth(i)
            if el.is_visible():
                text = el.text_content() or ""
                if text.strip().isdigit() and 2 <= int(text.strip()) <= 5:
                    visible_pages.append(el)

    if not visible_pages:
        return False

    if random.random() < 0.4:
        page_num = random.randint(2, 5)
        for el in visible_pages:
            text = el.text_content() or ""
            if text.strip() == str(page_num):
                try:
                    el.click()
                    print(f"  [Pagination] Clicked page {page_num}")
                    page.wait_for_timeout(1500)
                    return True
                except Exception:
                    return False

    return False


def check_daily_points(page: Page, max_retries: int = 3) -> tuple[int, int]:
    """Check current daily search points from the rewards dashboard.

    Args:
        page: Playwright page instance
        max_retries: Number of retry attempts for the entire flow (default 3)

    Returns:
        Tuple of (earned_points, max_points), or (-1, -1) if unable to retrieve.
    """
    for attempt in range(1, max_retries + 1):
        try:
            # Navigate to earn page (not dashboard) where points detail is available
            navigate_with_retry(page, "https://rewards.bing.com/earn")
            page.wait_for_timeout(2000)

            # Try to open the points detail panel by clicking "积分明细" button
            points_detail_selectors = [
                "text=积分明细",
                "button:has-text('积分明细')",
                "[aria-label*='积分明细']",
            ]

            panel_opened = False
            for selector in points_detail_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=3000):
                        print(f"[Points Check] Found '积分明细' button, clicking...")
                        btn.click()

                        # Wait for panel to actually open - poll for panel content
                        # The panel contains "必应搜索" and "/60" once opened
                        max_wait = 5  # seconds
                        waited = 0
                        while waited < max_wait:
                            page.wait_for_timeout(1000)
                            waited += 1

                            # Check if panel is open by looking for the specific pattern
                            try:
                                panel_text = page.inner_text("[role='dialog']")
                                if "必应搜索" in panel_text and "/60" in panel_text:
                                    panel_opened = True
                                    print(f"[Points Check] Points detail panel opened after {waited}s")
                                    break
                            except Exception:
                                continue

                        if not panel_opened:
                            # Try one more time with body text
                            page_text = page.inner_text("body")
                            if "必应搜索" in page_text and "/60" in page_text:
                                panel_opened = True
                                print(f"[Points Check] Panel content found in body after {waited}s")

                        break
                except Exception as e:
                    print(f"[Points Check] Selector '{selector}' failed: {e}")
                    continue

            if not panel_opened:
                print(f"[Points Check] Could not open points detail panel")

            # Get the panel or body content
            try:
                page_content = page.inner_text("[role='dialog']")
            except Exception:
                page_content = page.inner_text("body")

            print(f"[Points Check] Content length: {len(page_content)} chars")

            # Look for "必应搜索" followed by numbers X/Y
            # Pattern: "必应搜索" ... "15" ... "/60"
            match = re.search(r'必应搜索.*?(\d+)\s*/\s*(\d+)', page_content, re.DOTALL)
            if match:
                earned = int(match.group(1))
                maximum = int(match.group(2))
                print(f"[Points Check] Matched '必应搜索' pattern: {earned}/{maximum}")
                return (earned, maximum)

            # Alternative: look for just "搜索 X/Y"
            match = re.search(r'搜索.*?(\d+)\s*/\s*(\d+)', page_content, re.DOTALL)
            if match:
                earned = int(match.group(1))
                maximum = int(match.group(2))
                print(f"[Points Check] Matched '搜索' pattern: {earned}/{maximum}")
                return (earned, maximum)

            print(f"[Points Check] Could not find search progress, retrying ({attempt}/{max_retries})...")
            page.wait_for_timeout(1000)
            continue

        except Exception as e:
            print(f"[Points Check] Error: {e}, retrying ({attempt}/{max_retries})...")
            page.wait_for_timeout(1000)
            continue

    print(f"[Points Check] Failed after {max_retries} attempts, giving up")
    return (-1, -1)


def calculate_searches_needed(earned: int, maximum: int) -> int:
    """Calculate remaining searches needed based on points.

    Args:
        earned: Current points earned
        maximum: Maximum points available

    Returns:
        Number of searches needed
    """
    if earned < 0 or maximum <= 0:
        return config.DAILY_SEARCH_GOAL

    remaining_points = maximum - earned
    searches_needed = remaining_points // POINTS_PER_SEARCH
    return min(searches_needed, config.DAILY_SEARCH_GOAL)


def _get_default_search_terms() -> list:
    """Load default search terms from JSON file.

    Returns:
        List of search terms from JSON
    """
    global _SEARCH_TERMS_CACHE

    if _SEARCH_TERMS_CACHE is not None:
        return _SEARCH_TERMS_CACHE

    json_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'search_terms.json')

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _SEARCH_TERMS_CACHE = data.get('default_search_terms', [])
            return _SEARCH_TERMS_CACHE
    except Exception as e:
        print(f"[Search Terms] Error loading JSON: {e}")
        _SEARCH_TERMS_CACHE = []
        return _SEARCH_TERMS_CACHE


def perform_searches(page: Page, count: int) -> int:
    """Execute N searches and return the number completed.

    Args:
        page: Playwright page instance
        count: Number of searches to perform

    Returns:
        Number of searches successfully completed
    """
    completed = 0
    used_terms = set()

    search_terms = _get_default_search_terms().copy()
    random.shuffle(search_terms)

    for i in range(count):
        _close_extra_tabs(page)

        if not page.url.startswith(config.BING_URL) and 'bing.com' not in page.url.lower():
            page.goto(config.BING_URL)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(500)

        available_terms = [t for t in search_terms if t not in used_terms]
        if not available_terms:
            available_terms = _get_default_search_terms().copy()
            random.shuffle(available_terms)
            used_terms.clear()

        random_text = config.fetch_random_text()
        if random_text:
            term = random_text
        else:
            term = random.choice(available_terms)
        used_terms.add(term)

        print(f"Search {i + 1}/{count}: {term}")

        try:
            search_input = _get_search_input_on_current_page(page)
            random_delay_before_action()

            search_input.click()
            search_input.fill("")
            search_input.type(term, delay=random.randint(
                config.MIN_KEYSTROKE_DELAY_MS, config.MAX_KEYSTROKE_DELAY_MS
            ))

            page.keyboard.press("Enter")
            page.wait_for_timeout(1500)
            _try_random_pagination(page)

            if config.SEARCH_URL_PARAM in page.url or "search" in page.url.lower():
                completed += 1
                print(f"  -> Success!")
            else:
                print(f"  -> May have failed")

        except Exception as e:
            print(f"  -> Error: {e}")

        page.wait_for_timeout(random.randint(2000, 5000))

    return completed


def run(page: Page) -> dict:
    """Main entry point for daily search task.

    Args:
        page: Playwright page instance

    Returns:
        Result dictionary with state, earned, maximum, searches_needed,
        searches_completed, and success.
    """
    result = {
        "state": "search",
        "earned": 0,
        "maximum": 60,
        "searches_needed": 0,
        "searches_completed": 0,
        "success": False,
    }

    print("\n=== Daily Search Task ===")

    _close_extra_tabs(page)

    # Check daily points first - this navigates to rewards.bing.com/earn
    earned, maximum = check_daily_points(page)
    result["earned"] = earned
    result["maximum"] = maximum

    if earned >= 0 and maximum > 0:
        if earned >= maximum:
            print("[Pre-check] Daily search already at maximum!")
            # Close the rewards panel before returning
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            page.goto(config.BING_URL)
            page.wait_for_load_state("networkidle")
            result["searches_needed"] = 0
            result["success"] = True
            return result

        searches_needed = calculate_searches_needed(earned, maximum)
        result["searches_needed"] = searches_needed

        if searches_needed <= 0:
            print("[Pre-check] No searches needed based on current progress.")
            result["success"] = True
            return result

        print(f"[Pre-check] Points remaining: {maximum - earned}, searches needed: {searches_needed}")
    else:
        searches_needed = config.DAILY_SEARCH_GOAL
        result["searches_needed"] = searches_needed
        print(f"[Pre-check] Could not read points, performing {searches_needed} searches (default)")

    # Now go to Bing homepage to perform searches
    page.goto(config.BING_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    searches_completed = perform_searches(page, searches_needed)
    result["searches_completed"] = searches_completed

    earned, maximum = check_daily_points(page)
    if earned >= 0 and maximum > 0:
        print(f"[Post-check] Daily search progress: {earned}/{maximum}")

    print(f"Daily searches completed: {searches_completed}/{searches_needed}")
    result["success"] = searches_completed > 0 or result["searches_needed"] == 0

    return result
