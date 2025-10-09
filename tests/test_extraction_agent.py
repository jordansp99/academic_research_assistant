import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.extraction_agent import ExtractionAgent

class TestExtractionAgent(unittest.TestCase):

    @patch('agents.extraction_agent.requests.get')
    @patch('agents.extraction_agent.genai.GenerativeModel')
    def test_extract_metadata_from_web(self, mock_genai, mock_requests_get):
        # this test ensures that the extraction agent can correctly parse a mock html response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.content = "<html><head><title>Test Title</title></head><body><p>Test abstract</p></body></html>"
        mock_requests_get.return_value = mock_response

        mock_genai_instance = MagicMock()
        mock_genai.return_value = mock_genai_instance
        mock_genai_response = MagicMock()
        mock_genai_response.text = '''```json
{
  "title": "Test Title",
  "authors": ["Author 1", "Author 2"],
  "publication_date": "2023",
  "abstract": "Test abstract",
  "doi": "10.1234/12345"
}
```'''
        mock_genai_instance.generate_content.return_value = mock_genai_response

        agent = ExtractionAgent()
        paper_info = {'source': 'Web', 'url': 'http://example.com'}
        extracted_paper = agent.extract_metadata(paper_info)

        self.assertEqual(extracted_paper['title'], 'Test Title')
        self.assertEqual(extracted_paper['authors'], ['Author 1', 'Author 2'])
        self.assertEqual(extracted_paper['year'], '2023')
        self.assertEqual(extracted_paper['abstract'], 'Test abstract')
        self.assertEqual(extracted_paper['doi'], '10.1234/12345')

if __name__ == '__main__':
    unittest.main()
