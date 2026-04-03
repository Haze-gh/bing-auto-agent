"""Microsoft Rewards automation module."""
from rewards.activity_discovery import get_available_activities
from rewards.daily_search import perform_daily_searches
from rewards.activity_executor import execute_all_activities, execute_quiz, execute_poll, execute_smart_search

__all__ = [
    'get_available_activities',
    'perform_daily_searches',
    'execute_all_activities',
    'execute_quiz',
    'execute_poll',
    'execute_smart_search',
]
