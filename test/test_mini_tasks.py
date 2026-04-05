"""Test script for mini tasks detection and execution."""
import sys
from playwright.sync_api import sync_playwright
import config
from browser.edge_launcher import launch_edge_browser


def test_mini_tasks(page):
    """Test finding and parsing mini tasks on earn page."""
    print("\n" + "=" * 60)
    print("TEST: Mini Tasks Detection on Earn Page")
    print("=" * 60)

    # Navigate to earn page
    page.goto("https://rewards.bing.com/earn", timeout=15000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    # Check for #moreactivities section
    print("\n1. Checking #moreactivities section...")

    html_content = page.evaluate("document.body.innerHTML")
    has_moreactivities = 'id="moreactivities"' in html_content
    print(f"   HTML contains 'id=\"moreactivities\"': {has_moreactivities}")
    if has_moreactivities:
        idx = html_content.find('id="moreactivities"')
        print(f"   Found at position: {idx}")

    # Try to find the section
    moreactivities = page.locator("#moreactivities")
    if moreactivities.count() == 0:
        print("   [FAIL] #moreactivities not found!")
        return
    else:
        print(f"   [OK] #moreactivities found, count: {moreactivities.count()}")
        try:
            moreactivities.first.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)
            is_visible = moreactivities.first.is_visible()
            print(f"   #moreactivities visible after scroll: {is_visible}")
        except Exception as e:
            print(f"   Error checking visibility: {e}")

    print("\n2. Finding activity links in #moreactivities...")

    # Method 1: All links in #moreactivities
    links1 = page.locator("#moreactivities a").all()
    print(f"   Method 1 (#moreactivities a): {len(links1)} found")

    # Method 2: Links with bing.com/search
    links2 = page.locator("#moreactivities a[href*='bing.com']").all()
    print(f"   Method 2 (#moreactivities a[href*='bing.com']): {len(links2)} found")

    # Method 3: Links with microsoft-edge (should skip)
    links3 = page.locator("#moreactivities a[href^='microsoft-edge']").all()
    print(f"   Method 3 (#moreactivities a[href^='microsoft-edge']): {len(links3)} found")

    print("\n3. Analyzing activity links...")

    all_links = page.locator("#moreactivities a").all()

    incomplete_count = 0
    completed_count = 0

    for i, link in enumerate(all_links):
        try:
            if not link.is_visible():
                continue

            link_text = link.inner_text()
            href = link.get_attribute("href") or ""

            # Check completion status
            is_completed = "已完成" in link_text
            has_points_badge = "+" in link_text and not is_completed

            if is_completed:
                completed_count += 1
                status = "[已完成]"
            elif has_points_badge:
                incomplete_count += 1
                status = "[未完成]"
            else:
                status = "[无积分]"

            print(f"\n   [{i+1}] {status}")
            print(f"       Text: {link_text[:80].replace(chr(10), ' ')}")
            print(f"       URL: {href[:80]}")

            # Extract points if available
            import re
            points_match = re.search(r'\+(\d+)', link_text)
            if points_match:
                print(f"       Points: +{points_match.group(1)}")

        except Exception as e:
            print(f"   [{i+1}] Error: {e}")

    print(f"\n4. Summary:")
    print(f"   Completed: {completed_count}")
    print(f"   Incomplete: {incomplete_count}")
    print(f"   Total visible: {incomplete_count + completed_count}")

    return


def test_mini_task_interaction(page):
    """Test clicking and completing a mini task."""
    print("\n" + "=" * 60)
    print("TEST: Mini Task Interaction")
    print("=" * 60)

    page.goto("https://rewards.bing.com/earn", timeout=15000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    # Find first incomplete activity
    print("\n1. Finding first incomplete mini task...")

    all_links = page.locator("#moreactivities a").all()

    incomplete = None
    for link in all_links:
        try:
            if link.is_visible():
                text = link.inner_text()
                # Incomplete: has "+" but NOT "已完成"
                if "+" in text and "已完成" not in text:
                    href = link.get_attribute("href") or ""
                    # Skip non-actionable links
                    if not href.startswith("microsoft-edge:") and href:
                        incomplete = link
                        break
        except:
            continue

    if not incomplete:
        print("   No incomplete mini tasks found!")
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

    found_any = False
    for sel in selectors:
        try:
            elems = page.locator(sel).all()
            visible = [e for e in elems if e.is_visible()]
            if visible:
                found_any = True
                print(f"   {sel}: {len(visible)} visible elements")
                for i, e in enumerate(visible[:3]):
                    try:
                        print(f"      [{i}]: {e.inner_text()[:50].replace(chr(10), ' ')}")
                    except:
                        pass
        except:
            pass

    if not found_any:
        print("   No interactive elements found")

    return


def test_activity_types(page):
    """Test identifying different types of mini tasks."""
    print("\n" + "=" * 60)
    print("TEST: Mini Task Activity Types")
    print("=" * 60)

    page.goto("https://rewards.bing.com/earn", timeout=15000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    print("\n1. Categorizing activities by URL pattern...")

    # Categorize by URL
    url_categories = {
        "bing.com/search": [],
        "rewards.bing.com/redeem": [],
        "rewards.bing.com/referandearn": [],
        "aka.ms": [],
        "microsoft-edge": [],
        "other": [],
    }

    all_links = page.locator("#moreactivities a").all()

    for link in all_links:
        try:
            if not link.is_visible():
                continue
            href = link.get_attribute("href") or ""
            text = link.inner_text()[:30].replace(chr(10), ' ')

            if "bing.com/search" in href:
                url_categories["bing.com/search"].append(text)
            elif "rewards.bing.com/redeem" in href:
                url_categories["rewards.bing.com/redeem"].append(text)
            elif "rewards.bing.com/referandearn" in href:
                url_categories["rewards.bing.com/referandearn"].append(text)
            elif "aka.ms" in href:
                url_categories["aka.ms"].append(text)
            elif href.startswith("microsoft-edge"):
                url_categories["microsoft-edge"].append(text)
            else:
                url_categories["other"].append((text, href[:50]))
        except:
            continue

    for category, items in url_categories.items():
        if items:
            print(f"\n   {category}: {len(items)}")
            for item in items[:5]:
                if isinstance(item, tuple):
                    print(f"      - {item[0]}: {item[1]}")
                else:
                    print(f"      - {item}")

    return


def main():
    """Run all tests."""
    profile_name = sys.argv[1] if len(sys.argv) > 1 else "Default"
    profile_path = config.get_profile_path_from_config(0)

    print(f"Using profile: {profile_name}")
    print(f"Profile path: {profile_path}")

    with sync_playwright() as p:
        result = launch_edge_browser(
            p,
            headless=False,
            profile_path=profile_path
        )

        if isinstance(result, tuple):
            browser, context = result
            page = context.pages[0] if context.pages else context.new_page()
        else:
            browser = result
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()

        try:
            test_mini_tasks(page)
            test_activity_types(page)
            test_mini_task_interaction(page)

        finally:
            print("\n" + "=" * 60)
            print("Tests complete. Browser will stay open.")
            print("Press Enter to close...")
            input()
            browser.close()


if __name__ == "__main__":
    main()
