"""Integration test script for Microsoft Rewards automation.

Run actual task functions against a real browser to verify behavior.
Requires Microsoft Edge with a logged-in profile.

Usage:
    python test.py --dailyset -p "Profile 5"
    python test.py --search -p "Profile 5"
    python test.py --mini -p "Profile 5"
    python test.py --all -p "Profile 5"
"""
import argparse
import os
import sys

from playwright.sync_api import sync_playwright
import config
from browser.edge_launcher import launch_edge_browser
from search.bing_navigator import navigate_to_bing, verify_bing_loaded
from rewards.state_controller import run_day_set_only, run_mini_task_only, run_search_only, run_all


def main():
    parser = argparse.ArgumentParser(
        description="Test Microsoft Rewards automation tasks (real browser)"
    )
    parser.add_argument(
        "--profile", "-p", type=str, default="Default",
        help="Edge profile name to test with (default: Default)"
    )
    parser.add_argument(
        "--dailyset", action="store_true",
        help="Test daily set task only"
    )
    parser.add_argument(
        "--mini", action="store_true",
        help="Test mini task only"
    )
    parser.add_argument(
        "--search", action="store_true",
        help="Test search task only"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Test all tasks (full automation)"
    )

    args = parser.parse_args()

    if not any([args.dailyset, args.mini, args.search, args.all]):
        parser.print_help()
        return

    profile_path = os.path.join(config.PROFILE_BASE, args.profile)
    print(f"\n{'='*60}")
    print(f"TEST MODE: {args.profile}")
    print(f"Profile path: {profile_path}")
    print(f"{'='*60}")

    with sync_playwright() as p:
        result = launch_edge_browser(
            p,
            headless=config.HEADLESS,
            profile_path=profile_path
        )

        if isinstance(result, tuple):
            browser, context = result
        else:
            browser = result
            context = browser.new_context(viewport=config.VIEWPORT)

        page = context.pages[0] if context.pages else context.new_page()

        try:
            print("Navigating to Bing...")
            navigate_to_bing(page)

            if not verify_bing_loaded(page):
                print("Failed to load Bing search page")
                return

            print("Bing loaded successfully\n")

            if args.dailyset:
                print("=== TEST: Daily Set ===")
                result = run_day_set_only(page)
                print(f"Result: {result}")

            elif args.mini:
                print("=== TEST: Mini Task ===")
                result = run_mini_task_only(page)
                print(f"Result: {result}")

            elif args.search:
                print("=== TEST: Search ===")
                result = run_search_only(page)
                print(f"Result: {result}")

            elif args.all:
                print("=== TEST: Full Automation ===")
                result = run_all(page)
                print(f"Result: {result}")

        finally:
            print("\nClosing browser...")
            browser.close()

    print("\nDone!")


if __name__ == "__main__":
    main()
