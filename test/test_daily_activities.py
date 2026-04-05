"""Test script for daily activities detection and execution."""
import sys
import json
from playwright.sync_api import sync_playwright
import config
from browser.edge_launcher import launch_edge_browser


def test_daily_activities(page):
    """Test finding and parsing daily activities."""
    print("\n" + "=" * 60)
    print("TEST: Daily Activities Detection")
    print("=" * 60)

    # Navigate to rewards earn page
    page.goto("https://rewards.bing.com/dashboard", timeout=15000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    # Check for iframes
    print("\n0. Checking for iframes...")
    iframes = page.locator("iframe").all()
    print(f"   Found {len(iframes)} iframes on page")
    for i, iframe in enumerate(iframes):
        try:
            src = iframe.get_attribute("src") or "no src"
            visible = iframe.is_visible()
            print(f"   iframe[{i}]: src={src[:60]}, visible={visible}")
        except:
            print(f"   iframe[{i}]: could not get info")

    # Get page content for debugging
    print("\n1. Checking #dailyset section...")

    # Get HTML content directly via JavaScript
    print("   Getting HTML via JavaScript...")
    html_content = page.evaluate("document.body.innerHTML")
    has_dailyset = 'id="dailyset"' in html_content
    print(f"   HTML contains 'id=\"dailyset\"': {has_dailyset}")
    if has_dailyset:
        # Find position
        idx = html_content.find('id="dailyset"')
        print(f"   Found at position: {idx}")
        print(f"   Context: {html_content[idx:idx+200]}")

    # Try to find the dailyset section
    dailyset = page.locator("#dailyset")
    if dailyset.count() == 0:
        print("   [FAIL] #dailyset not found!")
    else:
        print(f"   [OK] #dailyset found, count: {dailyset.count()}")
        try:
            # Try scrolling to it
            dailyset.first.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)
            is_visible = dailyset.first.is_visible()
            print(f"   #dailyset visible after scroll: {is_visible}")

            # Get its HTML
            dailyset_html = dailyset.inner_html()
            print(f"   #dailyset HTML length: {len(dailyset_html)}")

            # Count activity links inside
            activity_links = page.locator("#dailyset a[href*='bing.com/search']").all()
            print(f"   Activity links inside #dailyset: {len(activity_links)}")

        except Exception as e:
            print(f"   Error checking visibility: {e}")

    # Find all activity links - try multiple locations
    print("\n2. Finding activity links...")

    # Method 1: Just find all links with bing.com/search on main page
    links1 = page.locator("a[href*='bing.com/search']").all()
    print(f"   Method 1 (all a[href*='bing.com/search']): {len(links1)} found")

    # Method 2: Look for #dailyset
    links2 = page.locator("#dailyset a[href*='bing.com/search']").all()
    print(f"   Method 2 (#dailyset a[href*='bing.com/search']): {len(links2)} found")

    # Method 3: Look for any elements containing specific activity text
    activity_texts = ["喜剧", "鲸歌", "炸豆丸子"]
    for text in activity_texts:
        elems = page.locator(f"text={text}").all()
        print(f"   Method 3 (text={text}): {len(elems)} found")

    print("\n3. Analyzing activity links found...")

    all_links = page.locator("a[href*='bing.com/search']").all()

    for i, link in enumerate(all_links):
        try:
            if not link.is_visible():
                continue

            link_text = link.inner_text()
            href = link.get_attribute("href") or ""

            # Check if completed:
            # - Has "已完成" text (completed)
            # - Has "+" in text without "已完成" (incomplete, has points badge)
            is_completed = "已完成" in link_text
            has_points_badge = "+" in link_text and not is_completed

            status = "[已完成]" if is_completed else "[未完成]" if has_points_badge else "[未知]"

            print(f"\n   [{i+1}] {status}")
            print(f"       Text: {link_text[:100].replace(chr(10), ' ')}")
            print(f"       URL: {href[:100]}")

        except Exception as e:
            print(f"   [{i+1}] Error: {e}")

    print("\n4. Looking for activity section with different selectors...")

    # Try to find the daily activities section
    section_selectors = [
        "#dailyset",
        "section[id*='daily']",
        "[class*='dailyset']",
        "text=每日活动",
        "text=每日",
    ]

    for sel in section_selectors:
        try:
            elems = page.locator(sel).all()
            visible_elems = [e for e in elems if e.is_visible()]
            if visible_elems:
                print(f"   [OK] {sel}: {len(visible_elems)} visible elements")
        except Exception as e:
            print(f"   [FAIL] {sel}: {e}")

    return


def test_points_panel(page):
    """Test the points panel on dashboard page."""
    print("\n" + "=" * 60)
    print("TEST: Points Panel on Dashboard")
    print("=" * 60)

    page.goto("https://rewards.bing.com/dashboard", timeout=15000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    print("\n1. Looking for points/card elements...")

    # Look for the "今日积分" card or similar
    card_selectors = [
        "text=今日积分",
        "[class*='title1']",
        ".text-title1",
    ]

    for sel in card_selectors:
        try:
            elems = page.locator(sel).all()
            visible = [e for e in elems if e.is_visible()]
            if visible:
                for e in visible[:3]:
                    text = e.inner_text()
                    print(f"   {sel}: '{text}'")
        except Exception as e:
            print(f"   {sel}: error - {e}")

    print("\n2. Looking for '积分明细' button...")

    btn = None
    for sel in ["text=积分明细", "button:has-text('积分明细')", "[aria-label*='积分明细']"]:
        try:
            elem = page.locator(sel).first
            if elem.is_visible(timeout=1000):
                print(f"   Found button with: {sel}")
                btn = elem
                break
        except:
            pass

    if btn:
        print("\n3. Clicking '积分明细' button...")
        try:
            btn.click()
            page.wait_for_timeout(2000)

            # Get all text from body
            body_text = page.inner_text("body")

            import re

            # Try to find the search progress
            patterns = [
                (r'必应搜索.*?(\d+)\s*/\s*(\d+)', 'pattern 1'),
                (r'搜索.*?(\d+)\s*/\s*(\d+)', 'pattern 2'),
                (r'今日积分.*?(\d+)', 'pattern 3'),
            ]

            found = False
            for pattern, name in patterns:
                match = re.search(pattern, body_text, re.DOTALL)
                if match:
                    print(f"   [OK] Found progress ({name}): {match.group(1)}/{match.group(2)}")
                    found = True
                    break

            if not found:
                print("   [FAIL] Could not find progress pattern")
                # Debug: show relevant parts
                if "必应搜索" in body_text:
                    idx = body_text.find("必应搜索")
                    print(f"   Context: ...{body_text[idx:idx+150]}...")

        except Exception as e:
            print(f"   Error: {e}")
    else:
        print("   '积分明细' button not found!")

    return


def test_activity_completion(page):
    """Test clicking and completing an activity."""
    print("\n" + "=" * 60)
    print("TEST: Activity Completion")
    print("=" * 60)

    page.goto("https://rewards.bing.com/dashboard", timeout=15000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    # Find first incomplete activity
    print("\n1. Finding first incomplete activity...")
    all_links = page.locator("a[href*='bing.com/search']").all()

    incomplete = None
    for link in all_links:
        try:
            if link.is_visible():
                text = link.inner_text()
                # Incomplete: has "+" but NOT "已完成"
                if "+" in text and "已完成" not in text:
                    incomplete = link
                    break
        except:
            continue

    if not incomplete:
        print("   No incomplete activities found!")
        return

    href = incomplete.get_attribute("href") or ""
    print(f"   URL: {href[:100]}")
    print(f"   Text: {incomplete.inner_text()[:100].replace(chr(10), ' ')}")

    # Click activity
    print("\n2. Clicking activity...")
    incomplete.click()
    page.wait_for_timeout(3000)

    print(f"   After click:")
    print(f"   Current URL: {page.url}")
    print(f"   Pages open: {len(page.context.pages)}")

    # If a new tab was opened, switch to it
    if len(page.context.pages) > 1:
        print("\n3. New tab detected, switching...")
        new_page = page.context.pages[-1]
        new_page.bring_to_front()
        page = new_page
        print(f"   Switched to: {page.url}")

    print(f"   Current URL: {page.url}")
    print(f"   Page title: {page.title()}")

    # Try to find interactive elements on current page
    print("\n4. Looking for interactive elements...")

    selectors = [
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

    for sel in selectors:
        try:
            elems = page.locator(sel).all()
            visible = [e for e in elems if e.is_visible()]
            if visible:
                print(f"   {sel}: {len(visible)} visible elements")
                # Get text of first few
                for i, e in enumerate(visible[:3]):
                    try:
                        print(f"      [{i}]: {e.inner_text()[:50].replace(chr(10), ' ')}")
                    except:
                        pass
        except:
            pass

    return


def main():
    """Run all tests."""
    profile_name = sys.argv[1] if len(sys.argv) > 1 else "Default"
    profile_path = config.get_profile_path_from_config(0)

    print(f"Using profile: {profile_name}")
    print(f"Profile path: {profile_path}")

    with sync_playwright() as p:
        # Use the same launch function as main.py
        result = launch_edge_browser(
            p,
            headless=False,
            profile_path=profile_path
        )

        # Handle both regular browser and persistent context (with profile)
        if isinstance(result, tuple):
            browser, context = result
            page = context.pages[0] if context.pages else context.new_page()
        else:
            browser = result
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()

        try:
            # Run tests
            test_daily_activities(page)
            test_points_panel(page)
            test_activity_completion(page)

        finally:
            print("\n" + "=" * 60)
            print("Tests complete. Browser will stay open.")
            print("Press Enter to close...")
            input()
            browser.close()


if __name__ == "__main__":
    main()
