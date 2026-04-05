"""Tests for mini_task module."""
import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMiniTask(unittest.TestCase):
    """Test cases for mini task."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_page = Mock()

    def test_run_returns_dict_structure(self):
        """Test that run returns expected dict structure."""
        from rewards.tasks.mini_task import run as mini_task_run

        with patch('rewards.tasks.mini_task.discover_mini_tasks', return_value=[]):
            self.mock_page.goto = Mock()
            self.mock_page.wait_for_load_state = Mock()
            self.mock_page.wait_for_timeout = Mock()
            self.mock_page.evaluate = Mock()
            self.mock_page.locator = Mock()

            result = mini_task_run(self.mock_page)

            self.assertIsInstance(result, dict)
            self.assertEqual(result['state'], 'mini_task')
            self.assertIn('attempted', result)
            self.assertIn('completed', result)
            self.assertIn('failed', result)
            self.assertIn('success', result)

    def test_discover_mini_tasks_filters_completed(self):
        """Test that discover_mini_tasks filters completed activities."""
        from rewards.tasks.mini_task import discover_mini_tasks

        mock_link = Mock()
        mock_link.is_visible = Mock(return_value=True)
        mock_link.inner_text = Mock(return_value="已完成的活动")

        self.mock_page.locator = Mock(return_value=Mock(all=Mock(return_value=[mock_link])))

        result = discover_mini_tasks(self.mock_page)

        self.assertEqual(len(result), 0)

    def test_discover_mini_tasks_filters_non_actionable(self):
        """Test that discover_mini_tasks filters non-actionable links."""
        from rewards.tasks.mini_task import discover_mini_tasks

        mock_link = Mock()
        mock_link.is_visible = Mock(return_value=True)
        mock_link.inner_text = Mock(return_value="Edge Link")
        mock_link.get_attribute = Mock(return_value="microsoft-edge://...")

        self.mock_page.locator = Mock(return_value=Mock(all=Mock(return_value=[mock_link])))

        result = discover_mini_tasks(self.mock_page)

        # Edge links should be filtered out
        self.assertEqual(len(result), 0)

    def test_discover_mini_tasks_includes_incomplete(self):
        """Test that discover_mini_tasks includes incomplete activities."""
        from rewards.tasks.mini_task import discover_mini_tasks

        mock_link = Mock()
        mock_link.is_visible = Mock(return_value=True)
        mock_link.inner_text = Mock(return_value="Quiz活动 +10")
        mock_link.get_attribute = Mock(return_value="https://rewards.bing.com/...")

        self.mock_page.locator = Mock(return_value=Mock(all=Mock(return_value=[mock_link])))

        result = discover_mini_tasks(self.mock_page)

        self.assertEqual(len(result), 1)


class TestMiniTaskExecute(unittest.TestCase):
    """Test execute_mini_task function."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_page = Mock()

    def test_execute_mini_task_clicks_link(self):
        """Test that execute_mini_task clicks the activity link."""
        from rewards.tasks.mini_task import execute_mini_task

        mock_link = Mock()
        mock_link.inner_text = Mock(return_value="Quiz活动 +10")
        mock_link.get_attribute = Mock(return_value="https://rewards.bing.com/...")

        mock_context = Mock()
        mock_context.pages = [self.mock_page]
        self.mock_page.context = mock_context

        with patch('rewards.tasks.mini_task._close_extra_tabs', return_value=0), \
             patch('rewards.tasks.mini_task._try_complete_activity_on_page', return_value=False):
            result = execute_mini_task(self.mock_page, mock_link)

        mock_link.click.assert_called_once()
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
