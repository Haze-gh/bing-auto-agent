"""Tests for day_set task module."""
import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDaySetTask(unittest.TestCase):
    """Test cases for day set task."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_page = Mock()

    def test_run_returns_dict_structure(self):
        """Test that run returns expected dict structure."""
        from rewards.tasks.day_set import run as day_set_run

        # Mock all internal functions
        with patch('rewards.tasks.day_set._close_rewards_panel'), \
             patch('rewards.tasks.day_set.discover_activities', return_value=[]):

            self.mock_page.goto = Mock()
            self.mock_page.wait_for_load_state = Mock()
            self.mock_page.wait_for_timeout = Mock()
            self.mock_page.evaluate = Mock()
            self.mock_page.locator = Mock()

            result = day_set_run(self.mock_page)

            self.assertIsInstance(result, dict)
            self.assertEqual(result['state'], 'day_set')
            self.assertIn('attempted', result)
            self.assertIn('completed', result)
            self.assertIn('failed', result)
            self.assertIn('success', result)

    def test_discover_activities_filters_completed(self):
        """Test that discover_activities filters out completed activities."""
        from rewards.tasks.day_set import discover_activities

        mock_link = Mock()
        mock_link.is_visible = Mock(return_value=True)
        mock_link.inner_text = Mock(return_value="已完成的活动")

        self.mock_page.locator = Mock(return_value=Mock(all=Mock(return_value=[mock_link])))

        result = discover_activities(self.mock_page)

        # Completed activities should be filtered out
        self.assertEqual(len(result), 0)

    def test_discover_activities_filters_no_points(self):
        """Test that discover_activities filters out activities without points."""
        from rewards.tasks.day_set import discover_activities

        mock_link = Mock()
        mock_link.is_visible = Mock(return_value=True)
        mock_link.inner_text = Mock(return_value="活动名称 (无符号)")

        self.mock_page.locator = Mock(return_value=Mock(all=Mock(return_value=[mock_link])))

        result = discover_activities(self.mock_page)

        # Activities without "+" should be filtered out
        self.assertEqual(len(result), 0)

    def test_discover_activities_includes_incomplete(self):
        """Test that discover_activities includes incomplete activities."""
        from rewards.tasks.day_set import discover_activities

        mock_link = Mock()
        mock_link.is_visible = Mock(return_value=True)
        mock_link.inner_text = Mock(return_value="Quiz活动 +5")

        self.mock_page.locator = Mock(return_value=Mock(all=Mock(return_value=[mock_link])))

        result = discover_activities(self.mock_page)

        # Should include the incomplete activity
        self.assertEqual(len(result), 1)


class TestDaySetExecuteActivity(unittest.TestCase):
    """Test execute_activity function."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_page = Mock()

    def test_execute_activity_clicks_link(self):
        """Test that execute_activity clicks the activity link."""
        from rewards.tasks.day_set import execute_activity

        mock_link = Mock()
        mock_link.inner_text = Mock(return_value="Quiz活动 +5")
        mock_link.get_attribute = Mock(return_value="https://bing.com/search?q=test")

        with patch('rewards.tasks.day_set._close_extra_tabs', return_value=0):
            result = execute_activity(self.mock_page, mock_link)

        mock_link.click.assert_called_once()
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
