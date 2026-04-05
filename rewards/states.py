"""State definitions for Microsoft Rewards automation."""
from enum import Enum


class State(Enum):
    """States for the rewards automation state machine."""
    INIT = "init"
    SEARCH = "search"
    DAY_SET = "day_set"
    MINI_TASK = "mini_task"
    DONE = "done"
    ERROR = "error"


# State transition map
NEXT_STATE = {
    State.INIT: State.SEARCH,
    State.SEARCH: State.DAY_SET,
    State.DAY_SET: State.MINI_TASK,
    State.MINI_TASK: State.DONE,
    State.ERROR: State.DONE,  # Stop on error
}
