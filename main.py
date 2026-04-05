"""Main entry point for Edge Browser Search Automation."""
import os
from playwright.sync_api import sync_playwright
import config
from browser.edge_launcher import launch_edge_browser
from search.bing_navigator import navigate_to_bing, verify_bing_loaded
from state.session_manager import save_state
from rewards import run_all, run_search_only, run_day_set_only, run_mini_task_only


def run_account_automation(p, profile_index: int, profile_name: str, args: dict):
    """Run automation for a single account/profile.

    Args:
        p: Playwright instance
        profile_index: Index of the profile in the list (unused, profile_name is used directly)
        profile_name: Name of the profile (for display)
        args: Command line arguments

    Returns:
        Dictionary with automation results
    """
    profile_path = os.path.join(config.PROFILE_BASE, profile_name)
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
            activity_results = {}
            day_set_result = run_day_set_only(page)
            activity_results['day_set'] = day_set_result
            mini_task_result = run_mini_task_only(page)
            activity_results['mini_task'] = mini_task_result
            print(f"\nActivity results: {activity_results}")
            results['activities'] = activity_results

        elif args['search_only']:
            print("\n=== SEARCH ONLY MODE ===")
            search_result = run_search_only(page)
            search_completed = search_result.get('search', {}).get('searches_completed', 0)
            print(f"\n搜索完成: {search_completed}/{args['search_count']}")
            results['search_completed'] = search_completed
            if search_completed == 0 and args['search_count'] > 0:
                print("[Info] Daily search already at maximum for this account.")
                print("[Info] Switching to next profile...")

        else:
            # Default: Execute all rewards tasks using state machine
            print("\n=== FULL REWARDS AUTOMATION MODE ===")
            all_results = run_all(page)
            print(f"\nState machine results: {all_results}")

            # Extract search results
            if 'search' in all_results:
                search_data = all_results['search']
                results['search_completed'] = search_data.get('searches_completed', 0)

            # Extract activity results
            if 'day_set' in all_results:
                results['activities']['day_set'] = all_results['day_set']
            if 'mini_task' in all_results:
                results['activities']['mini_task'] = all_results['mini_task']

            # Summary for this account
            print("\n" + "-" * 40)
            print(f"Account: {profile_name}")
            print(f"  Searches: {results['search_completed']}/{args['search_count']}")
            total_completed = sum(r.get('completed', 0) for r in results['activities'].values())
            total_attempted = sum(r.get('attempted', 0) for r in results['activities'].values())
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

    # Check if Windows
    is_windows = os.name == 'nt'

    if not os.isatty(0) or is_windows:
        # Non-interactive mode or Windows: select all by default
        return list(range(len(profile_names)))

    try:
        import termios
        import tty
    except ImportError:
        # termios not available (Windows without WSL)
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

    # Parse optional profile name (-p or --profile)
    new_profile_name = None
    for arg in sys.argv:
        if arg.startswith("-p=") or arg.startswith("--profile="):
            new_profile_name = arg.split("=", 1)[1].strip('"').strip("'")
            break

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
        'search_count': search_count,
        'new_profile_name': new_profile_name
    }

    # Get list of profiles (auto-detected or manual config)
    all_profile_names = config.get_all_profile_paths()

    # In login mode with -p, use the new profile directly
    if login_mode and new_profile_name:
        all_profile_names = [new_profile_name]
        selected_indices = [0]
        # Add to profiles.json immediately
        config.add_profile_to_config(new_profile_name)

    print(f"\n{'='*60}")
    print(f"Edge Browser Search Automation")
    print(f"Total accounts: {len(all_profile_names)}")
    print(f"{'='*60}")

    # TUI profile selector (skip in login mode or non-TTY)
    if login_mode:
        if not new_profile_name:
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
            total_completed = sum(res.get('completed', 0) for res in r['activities'].values())
            total_attempted = sum(res.get('attempted', 0) for res in r['activities'].values())
            print(f"  Activities: {total_completed}/{total_attempted} completed")

    print(f"\nTotal searches across all accounts: {total_searches}")
    print("\nDone!")


if __name__ == "__main__":
    main()
