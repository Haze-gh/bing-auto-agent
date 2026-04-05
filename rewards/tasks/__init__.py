"""Task modules for Microsoft Rewards automation."""

__all__ = [
    'search_run',
    'day_set_run',
    'mini_task_run',
]


def __getattr__(name):
    """Lazy import task run functions on first access."""
    if name == 'search_run':
        from rewards.tasks.search import run
        globals()['search_run'] = run
        return run
    elif name == 'day_set_run':
        from rewards.tasks.day_set import run
        globals()['day_set_run'] = run
        return run
    elif name == 'mini_task_run':
        from rewards.tasks.mini_task import run
        globals()['mini_task_run'] = run
        return run
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
