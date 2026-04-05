"""Tests for state controller module."""
import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestStateController(unittest.TestCase):
    """Test cases for state controller."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_page = Mock()

    def test_run_all_executes_all_states(self):
        """Test that run_all executes search, day_set, and mini_task."""
        from rewards.state_controller import run_all

        mock_search_result = {"state": "search", "success": True}
        mock_day_set_result = {"state": "day_set", "success": True}
        mock_mini_task_result = {"state": "mini_task", "success": True}

        with patch('rewards.state_controller.search_run', return_value=mock_search_result), \
             patch('rewards.state_controller.day_set_run', return_value=mock_day_set_result), \
             patch('rewards.state_controller.mini_task_run', return_value=mock_mini_task_result):

            result = run_all(self.mock_page)

            self.assertIn('search', result)
            self.assertIn('day_set', result)
            self.assertIn('mini_task', result)

    def test_run_all_stops_on_error(self):
        """Test that run_all stops execution on error."""
        from rewards.state_controller import run_all

        mock_search_result = {"state": "search", "success": False}

        with patch('rewards.state_controller.search_run', return_value=mock_search_result):
            result = run_all(self.mock_page)

            # Should only have search result since it failed
            self.assertIn('search', result)
            self.assertNotIn('day_set', result)

    def test_run_search_only(self):
        """Test run_search_only executes only search."""
        from rewards.state_controller import run_search_only

        mock_result = {"state": "search", "success": True, "searches_completed": 10}

        with patch('rewards.state_controller.search_run', return_value=mock_result):
            result = run_search_only(self.mock_page)

            self.assertIn('search', result)
            self.assertEqual(len(result), 1)


class TestStateDefinitions(unittest.TestCase):
    """Test state enum and transitions."""

    def test_state_enum_values(self):
        """Test State enum has expected values."""
        from rewards.states import State

        self.assertEqual(State.INIT.value, "init")
        self.assertEqual(State.SEARCH.value, "search")
        self.assertEqual(State.DAY_SET.value, "day_set")
        self.assertEqual(State.MINI_TASK.value, "mini_task")
        self.assertEqual(State.DONE.value, "done")
        self.assertEqual(State.ERROR.value, "error")

    def test_next_state_transitions(self):
        """Test NEXT_STATE transition map."""
        from rewards.states import State, NEXT_STATE

        self.assertEqual(NEXT_STATE[State.INIT], State.SEARCH)
        self.assertEqual(NEXT_STATE[State.SEARCH], State.DAY_SET)
        self.assertEqual(NEXT_STATE[State.DAY_SET], State.MINI_TASK)
        self.assertEqual(NEXT_STATE[State.MINI_TASK], State.DONE)
        self.assertEqual(NEXT_STATE[State.ERROR], State.DONE)


if __name__ == '__main__':
    unittest.main()
