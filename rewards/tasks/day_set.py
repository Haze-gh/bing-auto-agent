"""Daily set activities task for Microsoft Rewards."""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

import config
from search.bing_navigator import navigate_with_retry


def _close_rewards_panel(page: Page) -> None:
    """Close the rewards panel if it's open.

    Args:
        page: Playwright page instance
    """
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        close_selectors = [
            "#closeEduPanel",
            ".close_rewards_panel",
            "[aria-label*='close']",
        ]
        for selector in close_selectors:
            try:
                close_btn = page.locator(selector).first
                if close_btn.is_visible():
                    close_btn.click()
                    page.wait_for_timeout(500)
                    break
            except Exception:
                continue
    except Exception:
        pass


def _close_extra_tabs(page: Page) -> int:
    """Close all tabs except Bing/rewards pages.

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
            is_bing_page = (
                'bing.com' in tab_url or
                'rewards.bing.com' in tab_url or
                'rewards.microsoft.com' in tab_url
            )

            if not is_bing_page:
                tab.close()
                closed_count += 1
                print(f"[Tab Cleanup] Closed non-Bing tab: {tab_url[:60]}")

        if closed_count > 0:
            print(f"[Tab Cleanup] Closed {closed_count} extra tab(s)")
            page.wait_for_timeout(500)

    except Exception as e:
        print(f"[Tab Cleanup] Error closing tabs: {e}")

    return closed_count


def discover_activities(page: Page) -> list:
    """Find incomplete daily set activities.

    Args:
        page: Playwright page instance

    Returns:
        List of activity link elements
    """
    activity_links = page.locator("#dailyset a[href*='bing.com/search']").all()

    incomplete = []
    for link in activity_links:
        try:
            if not link.is_visible():
                continue

            link_text = link.inner_text()

            if "已完成" in link_text:
                print(f"[Daily Set] Skipping completed: {link_text[:30]}...")
                continue

            if "+" not in link_text:
                print(f"[Daily Set] Skipping (no points): {link_text[:30]}...")
                continue

            incomplete.append(link)

        except Exception:
            continue

    return incomplete


def execute_activity(page: Page, link) -> bool:
    """Execute a single daily set activity.

    Args:
        page: Playwright page instance
        link: Activity link locator

    Returns:
        True if completed, False otherwise
    """
    try:
        link_text = link.inner_text()
        href = link.get_attribute("href") or ""
        print(f"[Daily Set] Clicking: {link_text[:50]}...")
        print(f"   URL: {href[:80]}")

        link.click()
        page.wait_for_timeout(3000)

        page.wait_for_timeout(random.randint(
            config.ACTIVITY_DELAY_MIN, config.ACTIVITY_DELAY_MAX
        ))

        _close_extra_tabs(page)

        return True

    except Exception as e:
        print(f"[Daily Set] Activity error: {e}")
        return False


def run(page: Page) -> dict:
    """Main entry point for daily set task.

    Args:
        page: Playwright page instance

    Returns:
        Result dictionary with state, attempted, completed, failed, and success.
    """
    result = {
        "state": "day_set",
        "attempted": 0,
        "completed": 0,
        "failed": 0,
        "success": False,
    }

    print("\n=== Daily Set Task ===")

    _close_rewards_panel(page)

    try:
        navigate_with_retry(page, "https://rewards.bing.com/dashboard")
        page.wait_for_timeout(2000)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        activity_links = discover_activities(page)

        if not activity_links:
            print("[Daily Set] No daily activities found")
            result["success"] = True
            return result

        print(f"[Daily Set] Found {len(activity_links)} activity links")

        for link in activity_links:
            result["attempted"] += 1

            if execute_activity(page, link):
                result["completed"] += 1
            else:
                result["failed"] += 1

            navigate_with_retry(page, "https://rewards.bing.com/dashboard")
            page.wait_for_timeout(2000)

            activity_links = discover_activities(page)
            print(f"[Daily Set] Processed, {len(activity_links)} activities remaining")

        incomplete_count = 0
        for link in page.locator("#dailyset a[href*='bing.com/search']").all():
            try:
                if link.is_visible() and "+" in link.inner_text() and "已完成" not in link.inner_text():
                    incomplete_count += 1
            except:
                pass

        if incomplete_count == 0:
            print("[Daily Set] All activities completed!")
        else:
            print(f"[Daily Set] {incomplete_count} activities remaining")

    except Exception as e:
        print(f"[Daily Set] Error: {e}")

    print(f"[Daily Set] Summary: {result['completed']}/{result['attempted']} completed")
    result["success"] = result["failed"] == 0 or result["attempted"] > 0

    return result
