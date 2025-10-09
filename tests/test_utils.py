import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import can_fetch

class TestUtils(unittest.TestCase):

    @patch('utils.RobotFileParser')
    def test_can_fetch_allowed(self, mock_robot_parser):
        # a mock is used here to avoid making a real network request
        mock_rp_instance = MagicMock()
        mock_rp_instance.can_fetch.return_value = True
        mock_robot_parser.return_value = mock_rp_instance

        self.assertTrue(can_fetch("http://example.com/allowed"))
        mock_robot_parser.assert_called_once()
        mock_rp_instance.set_url.assert_called_once_with("http://example.com/robots.txt")
        mock_rp_instance.read.assert_called_once()
        mock_rp_instance.can_fetch.assert_called_once_with('*', "http://example.com/allowed")

    @patch('utils.RobotFileParser')
    def test_can_fetch_disallowed(self, mock_robot_parser):
        # a mock is used here to avoid making a real network request
        mock_rp_instance = MagicMock()
        mock_rp_instance.can_fetch.return_value = False
        mock_robot_parser.return_value = mock_rp_instance

        self.assertFalse(can_fetch("http://example.com/disallowed"))
        mock_robot_parser.assert_called_once()
        mock_rp_instance.set_url.assert_called_once_with("http://example.com/robots.txt")
        mock_rp_instance.read.assert_called_once()
        mock_rp_instance.can_fetch.assert_called_once_with('*', "http://example.com/disallowed")

if __name__ == '__main__':
    unittest.main()
