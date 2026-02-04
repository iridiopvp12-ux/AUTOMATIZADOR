import unittest
from unittest.mock import patch, MagicMock
import datetime
import os
import sys

# Mock flet correctly so DashboardView is a real class
mock_flet = MagicMock()
class MockColumn:
    def __init__(self, *args, **kwargs):
        self.controls = []
        pass
    def update(self):
        pass

mock_flet.Column = MockColumn
# We also need BarChart, Row, etc to be callable
mock_flet.BarChart = MagicMock()
mock_flet.Row = MagicMock()
mock_flet.Container = MagicMock()
mock_flet.Text = MagicMock()
mock_flet.IconButton = MagicMock()
mock_flet.Divider = MagicMock()
mock_flet.ListTile = MagicMock()
mock_flet.Icon = MagicMock()
mock_flet.border.all = MagicMock()
mock_flet.colors = MagicMock() # lowercase just in case
mock_flet.Colors = MagicMock()

sys.modules['flet'] = mock_flet

from src.views.dashboard_view import DashboardView

class TestDashboardLogic(unittest.TestCase):
    def setUp(self):
        self.dashboard = DashboardView()

    @patch('src.views.dashboard_view.glob.glob')
    @patch('src.views.dashboard_view.os.path.exists')
    def test_get_last_7_days_sessions(self, mock_exists, mock_glob):
        mock_exists.return_value = True

        def glob_side_effect(pattern):
            return ["file1.txt", "file2.txt"]

        mock_glob.side_effect = glob_side_effect

        data = self.dashboard.get_last_7_days_sessions()

        self.assertEqual(len(data), 7)
        self.assertIsInstance(data[0], tuple)
        self.assertEqual(len(data[0]), 2)

        for label, count in data:
            self.assertEqual(count, 2)

if __name__ == '__main__':
    unittest.main()
