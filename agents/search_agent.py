import os
import arxiv
import requests
import xml.etree.ElementTree as ET
from semanticscholar import SemanticScholar
from .base_agent import BaseAgent
import threading
from ddgs import DDGS

from logging_config import logger

class SearchAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.desires = {'find_papers'}
        s2_api_key = os.environ.get("S2_API_KEY")
        if s2_api_key:
            self.s2 = SemanticScholar(api_key=s2_api_key, timeout=10)
        else:
            # using the public api is fine, but an api key is better for performance
            self.s2 = SemanticScholar(timeout=10)
            logger.warning("Semantic Scholar API key not found. Set the S2_API_KEY environment variable for better performance.")
        self.arxiv_client = arxiv.Client(page_size=20, delay_seconds=3, num_retries=3)

    # this method is used to decide what the agent should do next
    def formulate_intentions(self, blackboard):
        if blackboard.get("query") and blackboard.get("papers") is None:
            self.intentions = [lambda: self.search_sources(blackboard)]
        else:
            self.intentions = []

    def search_sources(self, blackboard, s2_callback=None, s2_event=None, pubmed_callback=None, pubmed_event=None, arxiv_callback=None, arxiv_event=None, web_callback=None, web_event=None):
        query = blackboard["query"]
        arxiv_limit = blackboard.get("arxiv_limit", 20)
        s2_limit = blackboard.get("s2_limit", 20)
        pubmed_limit = blackboard.get("pubmed_limit", 20)
        ddg_limit = blackboard.get("ddg_limit", 20)
        search_arxiv_flag = blackboard.get("search_arxiv", True)
        search_s2_flag = blackboard.get("search_semantic_scholar", True)
        search_pubmed_flag = blackboard.get("search_pubmed", True)
        search_web_flag = blackboard.get("search_web", True)

        logger.info(f"Searching for: {query}...")

        # using threads here allows us to search all sources at once, which is much faster
        if search_arxiv_flag:
            arxiv_thread = threading.Thread(target=self.search_arxiv_thread, args=(query, arxiv_limit, arxiv_callback, arxiv_event))
            arxiv_thread.start()

        if search_s2_flag:
            s2_thread = threading.Thread(target=self.search_s2_thread, args=(query, s2_limit, s2_callback, s2_event))
            s2_thread.start()

        if search_pubmed_flag:
            pubmed_thread = threading.Thread(target=self.search_pubmed_thread, args=(query, pubmed_limit, pubmed_callback, pubmed_event))
            pubmed_thread.start()

        if search_web_flag:
            web_thread = threading.Thread(target=self.search_web_thread, args=(query, ddg_limit, web_callback, web_event))
            web_thread.start()

    def search_arxiv_thread(self, query, limit, callback=None, event=None):
        try:
            logger.info("Starting arXiv search...")
            search = arxiv.Search(
                query=query,
                max_results=limit,
                sort_by=arxiv.SortCriterion.Relevance
            )
            results = list(self.arxiv_client.results(search))
            logger.info("arXiv search finished.")
            arxiv_papers = [
                {
                    'title': result.title,
                    'url': result.pdf_url,
                    'authors': [author.name for author in result.authors],
                    'abstract': result.summary,
                    'source': 'arXiv',
                    'year': result.published.year,
                    'doi': result.doi
                }
                for result in results
            ]
            if callback:
                callback(arxiv_papers)
        except Exception as e:
            logger.error(f"An error occurred in the arXiv search thread: {e}")
        finally:
            if event:
                event.set()

    def search_s2_thread(self, query, limit, callback=None, event=None):
        try:
            logger.info("Starting Semantic Scholar search...")
            results = self.s2.search_paper(query, limit=limit, fields=['url', 'title', 'abstract', 'authors', 'year', 'venue', 'externalIds'])
            s2_papers_list = list(results)
            logger.info("Semantic Scholar search finished.")
            s2_papers = []
            for item in s2_papers_list:
                doi = item.get('externalIds', {}).get('DOI')
                s2_papers.append({
                    'title': item['title'],
                    'url': item['url'],
                    'authors': [author['name'] for author in item['authors']],
                    'abstract': item['abstract'],
                    'source': 'Semantic Scholar',
                    'year': item['year'],
                    'venue': item['venue'],
                    'doi': doi
                })
            if callback:
                callback(s2_papers)
        except Exception as e:
            logger.error(f"An error occurred in the Semantic Scholar search thread: {e}")
        finally:
            if event:
                event.set()

    def search_pubmed_thread(self, query, limit, callback=None, event=None):
        try:
            logger.info("Starting PubMed search...")
            base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
            search_url = f"{base_url}esearch.fcgi?db=pubmed&term={query.replace(' ', '+')}&retmax={limit}"
            response = requests.get(search_url)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            id_list = [id_elem.text for id_elem in root.findall(".//Id")]

            if not id_list:
                if callback:
                    callback([])
                return

            pubmed_papers = []
            for pmid in id_list:
                pubmed_papers.append({
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    'source': 'PubMed'
                })

            if callback:
                callback(pubmed_papers)

        finally:
            if event:
                event.set()

    def search_web_thread(self, query, limit, callback=None, event=None):
        try:
            logger.info("Starting Web search...")
            # filetype:pdf is used to increase the chances of finding a direct link to a pdf
            search_query = f"{query} academic papers filetype:pdf"
            logger.info(f"Searching DuckDuckGo for: {search_query}")
            with DDGS() as ddgs:
                results = list(ddgs.text(search_query, max_results=limit, region='uk-en', safesearch='moderate'))
            web_papers = [
                {
                    'url': result['href'],
                    'source': 'Web'
                }
                for result in results
            ]
            if callback:
                callback(web_papers)
        except Exception as e:
            logger.error(f"An error occurred in the Web search thread: {e}")
        finally:
            if event:
                event.set()
