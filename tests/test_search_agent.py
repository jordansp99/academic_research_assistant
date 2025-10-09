import unittest
from unittest.mock import MagicMock
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.search_agent import SearchAgent

class TestSearchAgent(unittest.TestCase):

    def test_formulate_intentions_with_query(self):
        agent = SearchAgent()
        blackboard = {"query": "test query"}
        agent.formulate_intentions(blackboard)
        self.assertEqual(len(agent.intentions), 1)

    def test_formulate_intentions_no_query(self):
        agent = SearchAgent()
        blackboard = {}
        agent.formulate_intentions(blackboard)
        self.assertEqual(len(agent.intentions), 0)

    def test_formulate_intentions_with_papers(self):
        agent = SearchAgent()
        blackboard = {"query": "test query", "papers": []}
        agent.formulate_intentions(blackboard)
        self.assertEqual(len(agent.intentions), 0)

if __name__ == '__main__':
    unittest.main()
