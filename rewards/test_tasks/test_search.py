"""Tests for search task module."""
import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSearchTask(unittest.TestCase):
    """Test cases for search task."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_page = Mock()

    def test_calculate_searches_needed(self):
        """Test calculate_searches_needed function."""
        from rewards.tasks.search import calculate_searches_needed

        # Test when earned < maximum
        result = calculate_searches_needed(30, 60)
        self.assertEqual(result, 10)  # (60-30)/3 = 10

        # Test when already maxed
        result = calculate_searches_needed(60, 60)
        self.assertEqual(result, 0)

        # Test when cannot read points
        result = calculate_searches_needed(-1, -1)
        self.assertEqual(result, 30)  # DAILY_SEARCH_GOAL default

    def test_run_returns_dict(self):
        """Test that run returns expected dict structure."""
        from rewards.tasks.search import run as search_run

        # Mock all internal functions
        with patch('rewards.tasks.search._close_extra_tabs', return_value=0), \
             patch('rewards.tasks.search.check_daily_points', return_value=(30, 60)), \
             patch('rewards.tasks.search.perform_searches', return_value=10), \
             patch('rewards.tasks.search.config.BING_URL', 'https://cn.bing.com'):

            self.mock_page.goto = Mock()
            self.mock_page.wait_for_load_state = Mock()
            self.mock_page.wait_for_timeout = Mock()
            self.mock_page.url = 'https://cn.bing.com'

            result = search_run(self.mock_page)

            self.assertIsInstance(result, dict)
            self.assertEqual(result['state'], 'search')
            self.assertIn('earned', result)
            self.assertIn('maximum', result)
            self.assertIn('searches_needed', result)
            self.assertIn('searches_completed', result)
            self.assertIn('success', result)


class TestSearchPointsConstants(unittest.TestCase):
    """Test POINTS_PER_SEARCH constant."""

    def test_points_per_search_value(self):
        """Test POINTS_PER_SEARCH is correct."""
        from rewards.tasks.search import POINTS_PER_SEARCH
        self.assertEqual(POINTS_PER_SEARCH, 3)


if __name__ == '__main__':
    unittest.main()
