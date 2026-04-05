"""Microsoft Rewards automation module.

This module provides lazy imports to avoid requiring playwright at import time.
"""

__all__ = [
    'get_available_activities',
    'run_all',
    'run_search_only',
    'run_day_set_only',
    'run_mini_task_only',
    'perform_daily_searches',
    'POINTS_PER_SEARCH',
]


def __getattr__(name):
    """Lazy import attributes on first access."""
    if name == 'get_available_activities':
        from rewards.activity_discovery import get_available_activities
        globals()['get_available_activities'] = get_available_activities
        return get_available_activities
    elif name in ('run_all', 'run_search_only', 'run_day_set_only', 'run_mini_task_only'):
        from rewards import state_controller
        val = getattr(state_controller, name)
        globals()[name] = val
        return val
    elif name == 'POINTS_PER_SEARCH':
        from rewards.tasks.search import POINTS_PER_SEARCH
        globals()['POINTS_PER_SEARCH'] = POINTS_PER_SEARCH
        return POINTS_PER_SEARCH
    elif name == 'perform_daily_searches':
        # Wrapper for backward compatibility - original perform_daily_searches returned int
        def perform_daily_searches(page, count=None):
            from rewards.tasks.search import run as search_run
            result = search_run(page)
            return result.get("searches_completed", 0)
        globals()['perform_daily_searches'] = perform_daily_searches
        return perform_daily_searches
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
