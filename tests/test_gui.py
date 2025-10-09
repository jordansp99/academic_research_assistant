import unittest
from unittest.mock import MagicMock, patch
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gui import MainWindow

# this is a workaround to be able to run the tests without a display
if os.environ.get("DISPLAY", "") == "":
    os.environ["QT_QPA_PLATFORM"] = "minimal"

from PyQt6.QtWidgets import QApplication

class TestGUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    def test_deduplication_in_gui(self):
        # this test ensures that the gui does not show duplicate papers
        window = MainWindow()
        papers = [
            {'title': 'Paper 1', 'authors': ['Author 1']},
            {'title': 'Paper 2', 'authors': ['Author 2']},
            {'title': 'Paper 1', 'authors': ['Author 1']},
        ]

        for paper in papers:
            window.add_paper_item(paper)

        self.assertEqual(window.results_list.count(), 2)

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()

if __name__ == '__main__':
    unittest.main()
