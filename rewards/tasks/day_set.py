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


def _close_overlay(page: Page) -> bool:
    """Close any blocking overlay/modal that may appear after activities.

    Args:
        page: Playwright page instance

    Returns:
        True if an overlay was closed, False otherwise
    """
    try:
        # Overlay typically has fixed positioning, high z-index, covers the screen
        overlay_selectors = [
            "div.fixed.inset-0.z-40",
            "[class*='fixed'][class*='inset-0'][class*='z-40']",
            "[class*='Smoke']",
            "[data-rac'][class*='fixed']",
        ]
        for sel in overlay_selectors:
            try:
                overlay = page.locator(sel).first
                if overlay.is_visible(timeout=2000):
                    # Try clicking the close button or pressing Escape
                    close_btns = [
                        overlay.locator("button").last,
                        overlay.locator("[aria-label*='close' i]").first,
                        overlay.locator("button[aria-label*='关']").first,
                    ]
                    for btn in close_btns:
                        try:
                            if btn.is_visible(timeout=1000):
                                btn.click()
                                page.wait_for_timeout(500)
                                return True
                        except Exception:
                            continue
                    # Fallback: press Escape
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def discover_activities(page: Page) -> list:
    """Find incomplete daily set activities.

    Args:
        page: Playwright page instance

    Returns:
        List of activity link elements
    """
    # Close any overlay that might block interactions
    _close_overlay(page)

    # Expand the DisclosurePanel to access hidden content
    expand_selectors = [
        "#dailyset button[aria-label*='每日活动']",
        "#dailyset button[aria-expanded='false']",
    ]
    for sel in expand_selectors:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=3000):
                page.evaluate(f"document.querySelector('{sel}').click()")
                page.wait_for_timeout(2000)
                break
        except Exception:
            continue

    # Find activity links inside #dailyset
    activity_links = page.locator("#dailyset a").all()

    incomplete = []
    for link in activity_links:
        try:
            href = link.get_attribute("href") or ""
            link_text = link.evaluate("el => el.textContent")

            # Skip non-Bing/rewards links
            if "rewards.bing.com" not in href and "bing.com" not in href:
                continue

            # Skip redeem links
            if "redeem" in href:
                continue

            if "已完成" in link_text:
                continue

            if "+" not in link_text:
                continue

            incomplete.append(link)

        except Exception:
            continue

    return incomplete


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


def execute_activity(page: Page, link) -> bool:
    """Execute a single daily set activity.

    Args:
        page: Playwright page instance
        link: Activity link locator

    Returns:
        True if completed, False otherwise
    """
    try:
        href = link.get_attribute("href") or ""
        link_text = link.evaluate("el => el.textContent")
        print(f"[Daily Set] Executing: {link_text[:50]}...")
        print(f"   URL: {href[:80]}")

        if not href:
            print("[Daily Set] ERROR: no href found")
            return False

        # Count tabs before click
        pages_before = len(page.context.pages)

        # Use JavaScript click via href selector (more reliable for this element)
        # Use encodeURIComponent to avoid quote escaping issues
        js_click = (
            f"document.querySelector('#dailyset a[href=\"{href}\"]').click()"
        )
        try:
            page.evaluate(js_click)
        except Exception:
            # Fallback: use CSS.escape for problematic characters
            js_click = (
                f"document.querySelector('#dailyset a[href=\"' + CSS.escape('{href}') + '\"]').click()"
            )
            try:
                page.evaluate(js_click)
            except Exception as e:
                print(f"[Daily Set] JS click failed: {e}")
                return False

        # Wait for new tab to open
        page.wait_for_timeout(3000)

        # Switch to new tab if opened
        context = page.context
        if len(context.pages) > pages_before:
            for tab in context.pages:
                if tab != page:
                    tab.bring_to_front()
                    page = tab
                    print(f"[Daily Set] Switched to new tab: {tab.url[:80]}")
                    break
        else:
            print("[Daily Set] WARNING: No new tab opened, using current page")

        page.wait_for_timeout(random.randint(
            config.ACTIVITY_DELAY_MIN, config.ACTIVITY_DELAY_MAX
        ))

        _try_complete_activity_on_page(page)
        _close_extra_tabs(page)

        print("[Daily Set] Activity executed successfully")
        return True

    except Exception as e:
        import traceback
        print(f"[Daily Set] Activity error: {e}")
        traceback.print_exc()
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

        # Check remaining incomplete activities - close overlay and expand panel
        _close_overlay(page)
        try:
            expand_btn = page.locator("#dailyset button[aria-expanded='false']").first
            if expand_btn.is_visible(timeout=3000):
                page.evaluate(
                    "document.querySelector('#dailyset button[aria-expanded=\"false\"]').click()"
                )
                page.wait_for_selector(
                    "#dailyset button[aria-expanded='true']",
                    timeout=5000
                )
                page.wait_for_timeout(2000)
        except Exception:
            pass

        incomplete_count = 0
        for link in page.locator("#dailyset a").all():
            try:
                href = link.get_attribute("href") or ""
                if "rewards.bing.com" not in href and "bing.com" not in href:
                    continue
                if "redeem" in href:
                    continue
                link_text = link.evaluate("el => el.textContent")
                if "+" in link_text and "已完成" not in link_text:
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
