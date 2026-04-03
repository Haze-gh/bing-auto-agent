"""Activity executor for Microsoft Rewards various activity types."""
from playwright.sync_api import Page
import random
import time
import config
from utils.human_behavior import random_delay_before_action


def execute_all_activities(page: Page) -> dict:
    """Execute all available Microsoft Rewards activities.

    Args:
        page: Playwright page instance

    Returns:
        Dictionary with results for each activity type
    """
    results = {
        'quizzes': {'attempted': 0, 'completed': 0, 'failed': 0},
        'polls': {'attempted': 0, 'completed': 0, 'failed': 0},
        'smart_searches': {'attempted': 0, 'completed': 0, 'failed': 0},
        'other': {'attempted': 0, 'completed': 0, 'failed': 0},
    }

    print("Starting rewards activities...")

    # Navigate to rewards dashboard
    try:
        page.goto("https://rewards.bing.com", timeout=15000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
    except Exception as e:
        print(f"Could not load rewards dashboard: {e}")
        # Try alternative URL
        try:
            page.goto(f"{config.BING_URL}/rewardsapp", timeout=15000)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
        except Exception as e2:
            print(f"Could not load rewards page: {e2}")

    # Execute quizzes
    results['quizzes'] = execute_quiz(page)

    # Execute polls
    results['polls'] = execute_poll(page)

    # Execute smart searches
    results['smart_searches'] = execute_smart_search(page)

    # Execute other activities
    results['other'] = execute_other_activities(page)

    print("\n=== Activity Summary ===")
    for activity_type, result in results.items():
        print(f"{activity_type}: {result['completed']}/{result['attempted']} completed")

    return results


def execute_quiz(page: Page) -> dict:
    """Execute quiz activities.

    Args:
        page: Playwright page instance

    Returns:
        Dictionary with attempted, completed, and failed counts
    """
    result = {'attempted': 0, 'completed': 0, 'failed': 0}

    print("\n--- Executing Quizzes ---")

    try:
        # Look for quiz cards/links
        quiz_selectors = [
            '[data-activity-type="quiz"]',
            '.quiz-card',
            '[href*="quiz"]',
            'text=Quiz',
            'text=测验',
            'text=问答',
        ]

        for selector in quiz_selectors:
            try:
                quiz_elements = page.locator(selector).all()
                for elem in quiz_elements:
                    if not elem.is_visible():
                        continue

                    result['attempted'] += 1
                    print(f"Found quiz element, attempting...")

                    try:
                        # Click to start quiz
                        elem.click()
                        page.wait_for_timeout(2000)

                        # Handle quiz questions
                        if _handle_quiz_questions(page):
                            result['completed'] += 1
                            print("  -> Quiz completed!")
                        else:
                            result['failed'] += 1
                            print("  -> Quiz failed/incomplete")

                        # Add delay between activities
                        page.wait_for_timeout(random.randint(
                            config.ACTIVITY_DELAY_MIN, config.ACTIVITY_DELAY_MAX
                        ))

                    except Exception as e:
                        result['failed'] += 1
                        print(f"  -> Quiz error: {e}")

            except Exception:
                continue

    except Exception as e:
        print(f"Quiz execution error: {e}")

    return result


def _handle_quiz_questions(page: Page) -> bool:
    """Handle quiz questions by selecting answers.

    Args:
        page: Playwright page instance

    Returns:
        True if quiz completed, False otherwise
    """
    try:
        # Wait for quiz to load
        page.wait_for_timeout(2000)

        # Look for answer options
        answer_selectors = [
            '[data-answer]',
            '.answer-option',
            '.quiz-option',
            '[role="radio"]',
            '[class*="answer"]',
        ]

        max_questions = 10  # Safety limit
        questions_answered = 0

        for _ in range(max_questions):
            # Try to find and click an answer
            answer_found = False
            for selector in answer_selectors:
                try:
                    answers = page.locator(selector).all()
                    for answer in answers:
                        if answer.is_visible() and answer.is_enabled():
                            # Click the answer
                            answer.click()
                            page.wait_for_timeout(500)
                            answer_found = True
                            questions_answered += 1
                            break
                except Exception:
                    continue

                if answer_found:
                    break

            if not answer_found:
                # No more answers found, quiz likely complete
                break

            # Wait between questions
            page.wait_for_timeout(random.randint(1000, 2000))

        # Look for submit/next button
        button_selectors = ['text=Submit', 'text=Next', 'text=提交', 'text=下一题', '[class*="next"]']
        for btn_selector in button_selectors:
            try:
                btn = page.get_by_text(btn_selector, exact=False).first
                if btn.is_visible():
                    btn.click()
                    page.wait_for_timeout(1000)
            except Exception:
                pass

        return questions_answered > 0

    except Exception as e:
        print(f"Error handling quiz questions: {e}")
        return False


def execute_poll(page: Page) -> dict:
    """Execute poll/voting activities.

    Args:
        page: Playwright page instance

    Returns:
        Dictionary with attempted, completed, and failed counts
    """
    result = {'attempted': 0, 'completed': 0, 'failed': 0}

    print("\n--- Executing Polls ---")

    try:
        # Look for poll cards/links
        poll_selectors = [
            '[data-activity-type="poll"]',
            '.poll-card',
            '[href*="poll"]',
            'text=Poll',
            'text=投票',
        ]

        for selector in poll_selectors:
            try:
                poll_elements = page.locator(selector).all()
                for elem in poll_elements:
                    if not elem.is_visible():
                        continue

                    result['attempted'] += 1
                    print(f"Found poll element, attempting...")

                    try:
                        # Click to start poll
                        elem.click()
                        page.wait_for_timeout(2000)

                        if _handle_poll_vote(page):
                            result['completed'] += 1
                            print("  -> Poll completed!")
                        else:
                            result['failed'] += 1
                            print("  -> Poll failed")

                        # Add delay between activities
                        page.wait_for_timeout(random.randint(
                            config.ACTIVITY_DELAY_MIN, config.ACTIVITY_DELAY_MAX
                        ))

                    except Exception as e:
                        result['failed'] += 1
                        print(f"  -> Poll error: {e}")

            except Exception:
                continue

    except Exception as e:
        print(f"Poll execution error: {e}")

    return result


def _handle_poll_vote(page: Page) -> bool:
    """Handle poll voting.

    Args:
        page: Playwright page instance

    Returns:
        True if poll completed, False otherwise
    """
    try:
        # Wait for poll to load
        page.wait_for_timeout(2000)

        # Look for voting options
        vote_selectors = [
            '[role="radio"]',
            '[role="option"]',
            '.poll-option',
            '.vote-option',
            '[class*="poll"]',
            '[class*="vote"]',
        ]

        voted = False
        for selector in vote_selectors:
            try:
                options = page.locator(selector).all()
                for option in options:
                    if option.is_visible() and option.is_enabled():
                        option.click()
                        page.wait_for_timeout(500)
                        voted = True
                        break
            except Exception:
                continue

            if voted:
                break

        if voted:
            # Look for submit button
            submit_selectors = ['text=Submit', 'text=Vote', 'text=提交', 'text=投票']
            for submit_text in submit_selectors:
                try:
                    submit_btn = page.get_by_text(submit_text, exact=False).first
                    if submit_btn.is_visible():
                        submit_btn.click()
                        page.wait_for_timeout(1000)
                        break
                except Exception:
                    pass

        return voted

    except Exception as e:
        print(f"Error handling poll vote: {e}")
        return False


def execute_smart_search(page: Page) -> dict:
    """Execute smart search activities.

    Args:
        page: Playwright page instance

    Returns:
        Dictionary with attempted, completed, and failed counts
    """
    result = {'attempted': 0, 'completed': 0, 'failed': 0}

    print("\n--- Executing Smart Searches ---")

    try:
        # Smart search activities often require visiting specific URLs
        # Look for links/buttons that indicate smart search
        smart_search_selectors = [
            '[data-activity-type="smart_search"]',
            '.smart-search',
            '[href*="smartsearch"]',
            'text=Smart Search',
            'text=智能搜索',
        ]

        for selector in smart_search_selectors:
            try:
                elements = page.locator(selector).all()
                for elem in elements:
                    if not elem.is_visible():
                        continue

                    result['attempted'] += 1
                    print(f"Found smart search element...")

                    try:
                        elem.click()
                        page.wait_for_timeout(3000)

                        # Verify we went to a search results page
                        if config.SEARCH_URL_PARAM in page.url or "search" in page.url.lower():
                            result['completed'] += 1
                        else:
                            result['failed'] += 1

                        # Add delay
                        page.wait_for_timeout(random.randint(
                            config.ACTIVITY_DELAY_MIN, config.ACTIVITY_DELAY_MAX
                        ))

                    except Exception as e:
                        result['failed'] += 1
                        print(f"  -> Smart search error: {e}")

            except Exception:
                continue

    except Exception as e:
        print(f"Smart search execution error: {e}")

    # Also try to execute searches for specific topics
    try:
        # Navigate to specific activity URLs if available
        activity_urls = [
            f"{config.BING_URL}/search?q=trivia+quiz",
            f"{config.BING_URL}/search?q=news+today",
            f"{config.BING_URL}/search?q=weather",
        ]

        for url in activity_urls:
            try:
                result['attempted'] += 1
                page.goto(url)
                page.wait_for_timeout(3000)

                if page.is_visible('input[name="q"]') or '#/search' in page.url:
                    result['completed'] += 1
                else:
                    result['failed'] += 1

                page.wait_for_timeout(random.randint(
                    config.ACTIVITY_DELAY_MIN, config.ACTIVITY_DELAY_MAX
                ))

            except Exception:
                result['failed'] += 1

    except Exception as e:
        print(f"Activity URL execution error: {e}")

    return result


def execute_other_activities(page: Page) -> dict:
    """Execute other available activities.

    Args:
        page: Playwright page instance

    Returns:
        Dictionary with attempted, completed, and failed counts
    """
    result = {'attempted': 0, 'completed': 0, 'failed': 0}

    print("\n--- Executing Other Activities ---")

    # Look for any clickable activity cards
    activity_selectors = [
        '[data-activity-type]',
        '.activity-card',
        '.rewards-card',
        '[class*="activity"]',
        '[class*="reward"]',
    ]

    for selector in activity_selectors:
        try:
            elements = page.locator(selector).all()
            for elem in elements:
                if not elem.is_visible():
                    continue

                # Skip already processed
                if elem.get_attribute('data-processed') == 'true':
                    continue

                result['attempted'] += 1

                try:
                    # Mark as processed
                    elem.set_attribute('data-processed', 'true')

                    # Get activity type for logging
                    activity_type = elem.get_attribute('data-activity-type') or 'unknown'
                    print(f"Found other activity: {activity_type}")

                    elem.click()
                    page.wait_for_timeout(2000)

                    # Try to complete the activity
                    if _try_complete_activity(page):
                        result['completed'] += 1
                    else:
                        result['failed'] += 1

                    # Navigate back
                    page.go_back()
                    page.wait_for_timeout(1000)

                    page.wait_for_timeout(random.randint(
                        config.ACTIVITY_DELAY_MIN, config.ACTIVITY_DELAY_MAX
                    ))

                except Exception as e:
                    result['failed'] += 1
                    print(f"  -> Activity error: {e}")

        except Exception:
            continue

    return result


def _try_complete_activity(page: Page) -> bool:
    """Try to complete any activity by interacting with common elements.

    Args:
        page: Playwright page instance

    Returns:
        True if some interaction happened, False otherwise
    """
    try:
        # Wait for activity to load
        page.wait_for_timeout(2000)

        # Look for common interactive elements
        interactive_selectors = [
            '[role="button"]',
            '[role="radio"]',
            '[role="checkbox"]',
            '[role="option"]',
            'button',
            'a[href]',
            '[class*="option"]',
            '[class*="choice"]',
        ]

        for selector in interactive_selectors:
            try:
                elements = page.locator(selector).all()
                for elem in elements:
                    if elem.is_visible() and elem.is_enabled():
                        # Try clicking
                        elem.click()
                        page.wait_for_timeout(500)
                        return True
            except Exception:
                continue

        return False

    except Exception:
        return False
