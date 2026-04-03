"""Main entry point for Edge Browser Search Automation."""
from playwright.sync_api import sync_playwright
import config
from browser.edge_launcher import launch_edge_browser
from search.bing_navigator import navigate_to_bing, verify_bing_loaded
from search.search_input import type_search_query, submit_search, verify_search_success
from state.session_manager import save_state
from utils.human_behavior import random_delay_before_action
from rewards.daily_search import perform_daily_searches
from rewards.activity_executor import execute_all_activities


def run_account_automation(p, profile_index: int, profile_name: str, args: dict):
    """Run automation for a single account/profile.

    Args:
        p: Playwright instance
        profile_index: Index of the profile in the list
        profile_name: Name of the profile (for display)
        args: Command line arguments

    Returns:
        Dictionary with automation results
    """
    import sys

    profile_path = config.get_profile_path_from_config(profile_index)
    print(f"\n{'='*60}")
    print(f"Starting automation for: {profile_name}")
    print(f"Profile path: {profile_path}")
    print(f"{'='*60}")

    # Launch browser with profile
    result = launch_edge_browser(
        p,
        headless=config.HEADLESS,
        profile_path=profile_path
    )

    # Handle both regular browser and persistent context (with profile)
    if isinstance(result, tuple):
        browser, context = result
        page = context.pages[0] if context.pages else context.new_page()
    else:
        browser = result
        context = browser.new_context(viewport=config.VIEWPORT)
        page = context.new_page()

    results = {
        'profile_name': profile_name,
        'search_completed': 0,
        'search_goal': args['search_count'],
        'activities': {}
    }

    try:
        # Navigate to Bing
        print("Navigating to Bing...")
        navigate_to_bing(page)

        if args['login_mode']:
            # Login mode: wait for user to manually login
            print("\n=== LOGIN MODE ===")
            print("Browser is open at Bing. Please login manually.")
            print("Press ENTER when done to save state and close browser...")
            input()
            save_state(context)
            return results

        # Verify Bing loaded
        if not verify_bing_loaded(page):
            print("Failed to load Bing search page")
            return results

        print("Bing loaded successfully")

        # Determine mode and execute
        if args['activities_only']:
            print("\n=== ACTIVITIES ONLY MODE ===")
            activity_results = execute_all_activities(page)
            print(f"\nActivity results: {activity_results}")
            results['activities'] = activity_results

        elif args['search_only']:
            print("\n=== SEARCH ONLY MODE ===")
            search_completed = perform_daily_searches(page, count=args['search_count'])
            print(f"\n搜索完成: {search_completed}/{args['search_count']}")
            results['search_completed'] = search_completed
            if search_completed == 0 and args['search_count'] > 0:
                print("[Info] Daily search already at maximum for this account.")
                print("[Info] Switching to next profile...")

        else:
            # Default: Execute all rewards tasks
            print("\n=== FULL REWARDS AUTOMATION MODE ===")

            # Execute daily searches
            print("\n--- Daily Searches ---")
            search_completed = perform_daily_searches(page, count=args['search_count'])
            print(f"搜索完成: {search_completed}/{args['search_count']}")
            results['search_completed'] = search_completed

            # If daily search already at maximum, skip to next profile
            if search_completed == 0 and args['search_count'] > 0:
                print("[Info] Daily search already at maximum for this account.")
                print("[Info] Skipping activities and switching to next profile...")
                return results

            # Execute all activity tasks
            print("\n--- Rewards Activities ---")
            activity_results = execute_all_activities(page)
            results['activities'] = activity_results

            # Summary for this account
            print("\n" + "-" * 40)
            print(f"Account: {profile_name}")
            print(f"  Searches: {search_completed}/{args['search_count']}")
            total_completed = sum(r['completed'] for r in activity_results.values())
            total_attempted = sum(r['attempted'] for r in activity_results.values())
            print(f"  Activities: {total_completed}/{total_attempted} completed")

        # Save state
        save_state(context)

    finally:
        # Close browser for this profile
        context.close()
        browser.close()

    return results


def select_profiles(profile_names: list[str]) -> list[int]:
    """TUI profile selector: arrow keys navigate, space toggle, enter confirm.

    Returns:
        List of selected indices into profile_names (at least one, defaults to all if cancelled)
    """
    import sys
    import os
    import termios
    import tty

    if not os.isatty(0):
        return list(range(len(profile_names)))

    def read_key():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                seq = sys.stdin.read(2)
                return ch + seq
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    selectable_indexes = list(range(len(profile_names)))
    selected = set(selectable_indexes)  # all selected by default
    cursor = 0

    def render():
        os.system("clear")
        print("=" * 50)
        print("  Edge Auto Agent - 选择要执行的 Profile")
        print("=" * 50)
        print(f"  共 {len(profile_names)} 个 Profile，空格切换选择，回车确认\n")
        for i, name in enumerate(profile_names):
            prefix = ">" if i == cursor else " "
            marker = "[x]" if i in selected else "[ ]"
            print(f"  {prefix} {marker}  {name}")
        print()
        print("  ↑/↓ 或 j/k 移动 | 空格切换 | A 全选 | N 全不选 | 回车确认")

    if selectable_indexes:
        render()
        while True:
            key = read_key()
            if key in ("\r", "\n"):
                break
            if key == " ":
                if cursor in selected:
                    selected.discard(cursor)
                else:
                    selected.add(cursor)
                render()
            elif key in ("\x1b[A", "k"):  # up
                cursor = max(cursor - 1, 0)
                render()
            elif key in ("\x1b[B", "j"):  # down
                cursor = min(cursor + 1, len(profile_names) - 1)
                render()
            elif key.lower() == "a":  # select all
                selected = set(selectable_indexes)
                render()
            elif key.lower() == "n":  # select none
                selected.clear()
                render()
            elif key == "\x03":  # Ctrl+C
                print("\n取消选择，默认全部执行。")
                return selectable_indexes

    if not selected:
        print("未选择任何 Profile，默认全部执行。")
        return selectable_indexes

    result = sorted(selected)
    selected_names = [profile_names[i] for i in result]
    print(f"\n已选择 {len(result)} 个 Profile: {selected_names}")
    return result


def main():
    """Main function to run Edge browser search automation for all accounts."""
    import sys

    # Check for mode flags
    login_mode = "--login" in sys.argv or "-l" in sys.argv
    search_only = "--search-only" in sys.argv
    activities_only = "--activities-only" in sys.argv

    # Parse optional search count
    search_count = config.DAILY_SEARCH_GOAL
    for arg in sys.argv:
        if arg.startswith("--searches="):
            try:
                search_count = int(arg.split("=")[1])
            except ValueError:
                pass

    args = {
        'login_mode': login_mode,
        'search_only': search_only,
        'activities_only': activities_only,
        'search_count': search_count
    }

    # Get list of profiles (auto-detected or manual config)
    all_profile_names = config.get_all_profile_paths()

    print(f"\n{'='*60}")
    print(f"Edge Browser Search Automation")
    print(f"Total accounts: {len(all_profile_names)}")
    print(f"{'='*60}")

    # TUI profile selector (skip in login mode or non-TTY)
    if login_mode:
        selected_indices = [0] if all_profile_names else []
    else:
        selected_indices = select_profiles(all_profile_names)

    all_results = []

    with sync_playwright() as p:
        for seq_idx, global_idx in enumerate(selected_indices):
            profile_name = all_profile_names[global_idx]
            results = run_account_automation(p, global_idx, profile_name, args)
            all_results.append(results)

            # Small delay between accounts
            if seq_idx < len(selected_indices) - 1:
                import time
                print("\n[Info] Switching to next account...")
                time.sleep(2)

    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY - ALL ACCOUNTS")
    print(f"{'='*60}")

    total_searches = 0
    for r in all_results:
        print(f"\n{r['profile_name']}:")
        print(f"  Searches: {r['search_completed']}/{r['search_goal']}")
        total_searches += r['search_completed']

        if r['activities']:
            total_completed = sum(res['completed'] for res in r['activities'].values())
            total_attempted = sum(res['attempted'] for res in r['activities'].values())
            print(f"  Activities: {total_completed}/{total_attempted} completed")

    print(f"\nTotal searches across all accounts: {total_searches}")
    print("\nDone!")


if __name__ == "__main__":
    main()
