"""Activity discovery for Microsoft Rewards."""
from playwright.sync_api import Page
import config


def get_available_activities(page: Page) -> list[dict]:
    """Get all available Microsoft Rewards activities.

    Args:
        page: Playwright page instance

    Returns:
        List of activity dictionaries with type and remaining count
    """
    activities = []

    try:
        # Navigate to Bing Rewards page
        rewards_url = f"{config.BING_URL}/rewardsapp"
        page.goto(rewards_url, timeout=10000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Look for activity cards on the page
        # Microsoft Rewards page structure varies, so we try multiple selectors

        # Method 1: Look for activity items by common class patterns
        activity_selectors = [
            '.rewards-card',
            '.activity-item',
            '[data-activity-type]',
            '.bt_pill',
            '.promo_Item',
        ]

        for selector in activity_selectors:
            items = page.locator(selector).all()
            for item in items:
                if item.is_visible():
                    activity_type = item.get_attribute('data-activity-type') or item.inner_text()[:50]
                    activities.append({
                        'type': activity_type,
                        'element': item,
                    })

        # Method 2: Check for specific activity types by text
        quiz_texts = ['Quiz', 'quiz', '问答', '测验']
        poll_texts = ['Poll', 'poll', '投票']
        search_texts = ['Search', 'search', '搜索', 'Smart Search']

        for text in quiz_texts:
            if page.get_by_text(text, exact=False).first.is_visible():
                activities.append({'type': 'quiz', 'text_search': text})

        for text in poll_texts:
            if page.get_by_text(text, exact=False).first.is_visible():
                activities.append({'type': 'poll', 'text_search': text})

        for text in search_texts:
            if page.get_by_text(text, exact=False).first.is_visible():
                activities.append({'type': 'search', 'text_search': text})

    except Exception as e:
        print(f"Error discovering activities: {e}")

    # Also try to get activities from the dashboard
    try:
        dashboard_url = "https://rewards.bing.com"
        page.goto(dashboard_url, timeout=10000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Look for remaining points/changes indicators
        remaining_elements = page.locator('[class*="remaining"], [class*="count"], [data-remaining]').all()
        for elem in remaining_elements:
            if elem.is_visible():
                text = elem.inner_text()
                if text and any(c.isdigit() for c in text):
                    activities.append({
                        'type': 'points_indicator',
                        'text': text[:100],
                    })

    except Exception as e:
        print(f"Error checking rewards dashboard: {e}")

    return activities


def check_activity_availability(page: Page) -> dict:
    """Check what activities are currently available.

    Args:
        page: Playwright page instance

    Returns:
        Dictionary with availability info for each activity type
    """
    return {
        'searches_available': _check_search_availability(page),
        'quizzes_available': _check_quiz_availability(page),
        'polls_available': _check_poll_availability(page),
        'other_available': _check_other_activities(page),
    }


def _check_search_availability(page: Page) -> int:
    """Check how many daily searches are still available.

    Returns:
        Number of searches remaining (0 if unknown)
    """
    try:
        # Look for search progress indicators
        selectors = [
            '[data-search-remaining]',
            '.search-progress',
            '[class*="searchRemaining"]',
        ]
        for selector in selectors:
            elem = page.locator(selector).first
            if elem.is_visible():
                text = elem.inner_text()
                # Extract number from text like "15/30"
                import re
                match = re.search(r'(\d+)/(\d+)', text)
                if match:
                    remaining = int(match.group(1))
                    return remaining
    except Exception:
        pass
    return 0


def _check_quiz_availability(page: Page) -> int:
    """Check how many quizzes are still available.

    Returns:
        Number of quizzes remaining (0 if unknown)
    """
    try:
        selectors = [
            '[data-quiz-remaining]',
            '.quiz-progress',
            '[class*="quizRemaining"]',
        ]
        for selector in selectors:
            elem = page.locator(selector).first
            if elem.is_visible():
                text = elem.inner_text()
                import re
                match = re.search(r'(\d+)', text)
                if match:
                    return int(match.group(1))
    except Exception:
        pass
    return 0


def _check_poll_availability(page: Page) -> int:
    """Check how many polls are still available.

    Returns:
        Number of polls remaining (0 if unknown)
    """
    try:
        selectors = [
            '[data-poll-remaining]',
            '.poll-progress',
        ]
        for selector in selectors:
            elem = page.locator(selector).first
            if elem.is_visible():
                text = elem.inner_text()
                import re
                match = re.search(r'(\d+)', text)
                if match:
                    return int(match.group(1))
    except Exception:
        pass
    return 0


def _check_other_activities(page: Page) -> list:
    """Check for other available activities.

    Returns:
        List of other activity types available
    """
    other = []
    try:
        # Look for activity cards or links
        activity_keywords = ['ABC', 'Weekly', 'Daily', 'Poll', 'Quiz', 'Search', 'Click', 'Tap']
        for keyword in activity_keywords:
            if page.get_by_text(keyword, exact=False).first.is_visible():
                if keyword not in other:
                    other.append(keyword)
    except Exception:
        pass
    return other
