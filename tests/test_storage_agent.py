import unittest
from unittest.mock import patch, mock_open
import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.storage_agent import StorageAgent

class TestStorageAgent(unittest.TestCase):

    def test_deduplication(self):
        # this test ensures that the storage agent correctly removes duplicate papers
        papers = [
            {'doi': '1', 'title': 'Paper 1'},
            {'doi': '2', 'title': 'Paper 2'},
            {'doi': '1', 'title': 'Paper 1 Duplicate'},
            {'url': 'http://example.com/3', 'title': 'Paper 3'},
            {'url': 'http://example.com/4', 'title': 'Paper 4'},
            {'url': 'http://example.com/3', 'title': 'Paper 3 Duplicate'},
        ]
        agent = StorageAgent()
        blackboard = {"extracted_data": papers}

        m = mock_open()
        with patch("builtins.open", m):
            agent.run(blackboard)

        m.assert_called_once_with('research_digest.json', 'w', encoding='utf-8')
        handle = m()
        written_data = json.loads("".join(c[0][0] for c in handle.write.call_args_list))
        self.assertEqual(len(written_data), 4)
        self.assertEqual(written_data[0]['title'], 'Paper 1')
        self.assertEqual(written_data[1]['title'], 'Paper 2')
        self.assertEqual(written_data[2]['title'], 'Paper 3')
        self.assertEqual(written_data[3]['title'], 'Paper 4')

if __name__ == '__main__':
    unittest.main()
