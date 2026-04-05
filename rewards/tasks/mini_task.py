"""Mini tasks from earn page for Microsoft Rewards."""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

import config
from search.bing_navigator import navigate_with_retry


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


def _try_complete_activity_on_page(page: Page) -> bool:
    """Try to complete an activity by interacting with common elements.

    Args:
        page: Playwright page instance

    Returns:
        True if some interaction happened, False otherwise
    """
    try:
        page.wait_for_timeout(2000)

        interactive_selectors = [
            "[role='radio']",
            "[role='checkbox']",
            "[role='option']",
            "button",
            ".quiz-option",
            ".poll-option",
            "[class*='option']",
            "[class*='choice']",
            "[class*='quiz']",
            "[class*='poll']",
        ]

        for selector in interactive_selectors:
            try:
                elements = page.locator(selector).all()
                for elem in elements:
                    if elem.is_visible() and elem.is_enabled():
                        elem.click()
                        page.wait_for_timeout(500)
                        return True
            except Exception:
                continue

        return False

    except Exception:
        return False


def discover_mini_tasks(page: Page) -> list:
    """Find incomplete mini tasks from the earn page.

    Args:
        page: Playwright page instance

    Returns:
        List of activity link elements
    """
    activity_links = page.locator("#moreactivities a").all()

    incomplete = []
    for link in activity_links:
        try:
            if not link.is_visible():
                continue

            link_text = link.inner_text()

            if "已完成" in link_text:
                print(f"[Mini Tasks] Skipping completed: {link_text[:40]}...")
                continue

            if "+" not in link_text:
                href = link.get_attribute("href") or ""
                if href.startswith("microsoft-edge:") or not href:
                    print(f"[Mini Tasks] Skipping non-actionable: {link_text[:40]}...")
                    continue
                print(f"[Mini Tasks] Skipping (no points): {link_text[:40]}...")
                continue

            incomplete.append(link)

        except Exception:
            continue

    return incomplete


def execute_mini_task(page: Page, link) -> bool:
    """Execute a single mini task.

    Args:
        page: Playwright page instance
        link: Activity link locator

    Returns:
        True if completed, False otherwise
    """
    try:
        link_text = link.inner_text()
        href = link.get_attribute("href") or ""
        print(f"[Mini Tasks] Clicking: {link_text[:50]}...")
        print(f"   URL: {href[:80]}")

        link.click()
        page.wait_for_timeout(2000)

        context = page.context
        if len(context.pages) > 1:
            for tab in context.pages:
                if tab != page:
                    tab.bring_to_front()
                    page = tab
                    print(f"   [Tab] Switched to new tab: {tab.url[:60]}")
                    break

        page.wait_for_timeout(random.randint(
            config.ACTIVITY_DELAY_MIN, config.ACTIVITY_DELAY_MAX
        ))

        _try_complete_activity_on_page(page)
        _close_extra_tabs(page)

        if page.url != "https://rewards.bing.com/earn":
            navigate_with_retry(page, "https://rewards.bing.com/earn")
            page.wait_for_timeout(2000)

        return True

    except Exception as e:
        print(f"[Mini Tasks] Activity error: {e}")
        return False


def run(page: Page) -> dict:
    """Main entry point for mini task.

    Args:
        page: Playwright page instance

    Returns:
        Result dictionary with state, attempted, completed, failed, and success.
    """
    result = {
        "state": "mini_task",
        "attempted": 0,
        "completed": 0,
        "failed": 0,
        "success": False,
    }

    print("\n=== Mini Task ===")

    try:
        navigate_with_retry(page, "https://rewards.bing.com/earn")
        page.wait_for_timeout(2000)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        activity_links = discover_mini_tasks(page)

        if not activity_links:
            print("[Mini Tasks] No mini tasks found")
            result["success"] = True
            return result

        print(f"[Mini Tasks] Found {len(activity_links)} activity links")

        for link in activity_links:
            result["attempted"] += 1

            if execute_mini_task(page, link):
                result["completed"] += 1
            else:
                result["failed"] += 1

            activity_links = page.locator("#moreactivities a").all()
            print(f"[Mini Tasks] Processed, {len(activity_links)} activities remaining")

        incomplete_count = 0
        for link in page.locator("#moreactivities a").all():
            try:
                if link.is_visible():
                    text = link.inner_text()
                    if "+" in text and "已完成" not in text:
                        incomplete_count += 1
            except:
                pass

        if incomplete_count == 0:
            print("[Mini Tasks] All mini tasks completed!")
        else:
            print(f"[Mini Tasks] {incomplete_count} mini tasks remaining")

    except Exception as e:
        print(f"[Mini Tasks] Error: {e}")

    print(f"[Mini Tasks] Summary: {result['completed']}/{result['attempted']} completed")
    result["success"] = result["failed"] == 0 or result["attempted"] > 0

    return result
