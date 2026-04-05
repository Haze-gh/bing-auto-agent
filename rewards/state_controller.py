"""State machine orchestrator for Microsoft Rewards automation."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

from rewards.states import State, NEXT_STATE
from rewards.tasks.search import run as search_run
from rewards.tasks.day_set import run as day_set_run
from rewards.tasks.mini_task import run as mini_task_run


def run_all(page: Page) -> dict:
    """Run full automation through state machine.

    Args:
        page: Playwright page instance

    Returns:
        Dictionary with results for each state
    """
    results = {}
    current_state = State.INIT

    state_handlers = {
        State.SEARCH: search_run,
        State.DAY_SET: day_set_run,
        State.MINI_TASK: mini_task_run,
    }

    while current_state != State.DONE:
        if current_state in state_handlers:
            result = state_handlers[current_state](page)
            results[current_state.value] = result

            if not result.get("success", False):
                current_state = State.ERROR
            else:
                current_state = NEXT_STATE[current_state]
        else:
            current_state = NEXT_STATE[current_state]

    return results


def run_search_only(page: Page) -> dict:
    """Run search task only.

    Args:
        page: Playwright page instance

    Returns:
        Dictionary with search result
    """
    result = search_run(page)
    return {"search": result}


def run_day_set_only(page: Page) -> dict:
    """Run daily set task only.

    Args:
        page: Playwright page instance

    Returns:
        Dictionary with day_set result
    """
    result = day_set_run(page)
    return {"day_set": result}


def run_mini_task_only(page: Page) -> dict:
    """Run mini task only.

    Args:
        page: Playwright page instance

    Returns:
        Dictionary with mini_task result
    """
    result = mini_task_run(page)
    return {"mini_task": result}
