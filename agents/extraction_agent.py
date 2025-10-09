import time
import requests
import xml.etree.ElementTree as ET
import re
import io
import pdfplumber
from bs4 import BeautifulSoup
from .base_agent import BaseAgent
import os
import google.generativeai as genai
import json

from dotenv import load_dotenv

from logging_config import logger

class ExtractionAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.desires = {'extract_metadata'}
        load_dotenv()
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.model = genai.GenerativeModel('models/gemini-flash-lite-latest')

    def formulate_intentions(self, blackboard):
        self.intentions = []
        papers = blackboard.get("papers", [])
        for paper in papers:
            if not paper.get('abstract') or not paper.get('authors'):
                self.intentions.append(lambda p=paper: self.extract_metadata(p))

    def extract_metadata(self, paper_info: dict) -> dict:
        if paper_info.get('abstract') and paper_info.get('authors'):
            return paper_info

        url = paper_info.get('url')
        if not url:
            return {**paper_info, 'authors': [], 'abstract': 'N/A'}

        logger.info(f"Extracting missing metadata from: {url}")

        if "pubmed.ncbi.nlm.nih.gov" in url:
            try:
                time.sleep(1)
                pmid = url.strip('/').split('/')[-1]
                base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
                fetch_url = f"{base_url}efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"

                api_response = requests.get(fetch_url, timeout=15)
                api_response.raise_for_status()
                root = ET.fromstring(api_response.content)
                article = root.find(".//PubmedArticle")

                if article:
                    logger.info(f"Successfully extracted metadata for {url} from API.")
                    title_element = article.find(".//ArticleTitle")
                    paper_info['title'] = title_element.text if title_element is not None else "N/A"
                    author_list = article.findall(".//Author")
                    authors = []
                    for author in author_list:
                        last_name = author.find("LastName")
                        fore_name = author.find("ForeName")
                        if last_name is not None and fore_name is not None:
                            authors.append(f"{fore_name.text} {last_name.text}")
                    paper_info['authors'] = authors if authors else ['N/A']
                    abstract_text_elements = article.findall(".//Abstract/AbstractText")
                    paper_info['abstract'] = " ".join([elem.text for elem in abstract_text_elements if elem.text]) or 'N/A'
                    journal_title_element = article.find(".//Journal/Title")
                    paper_info['venue'] = journal_title_element.text if journal_title_element is not None else 'N/A'
                    pub_date_element = article.find(".//PubDate/Year")
                    year = "N/A"
                    if pub_date_element is not None:
                        year = pub_date_element.text
                    else:
                        medline_date = article.find(".//MedlineDate")
                        if medline_date is not None and medline_date.text:
                            match = re.search(r'\d{4}', medline_date.text)
                            if match:
                                year = match.group(0)
                    paper_info['year'] = year
                    doi_element = article.find(".//ArticleId[@IdType='doi']")
                    paper_info['doi'] = doi_element.text if doi_element is not None else 'N/A'
                    return paper_info

            except (requests.exceptions.RequestException, ET.ParseError) as e:
                logger.error(f"PubMed API call failed for {url}: {e}")
                return {**paper_info, 'title': 'Extraction Failed', 'authors': [], 'abstract': 'Extraction Failed'}


        elif paper_info.get('source') == 'Web':
            url = paper_info.get('url')
            if not url:
                return {**paper_info, 'authors': [], 'abstract': 'N/A'}

            logger.info(f"Fetching URL: {url}")
            try:
                response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
                response.raise_for_status()

                content_type = response.headers.get('content-type', '')

                if 'application/pdf' in content_type:
                    logger.info(f"PDF detected, parsing content from: {url}")
                    with io.BytesIO(response.content) as pdf_file:
                        with pdfplumber.open(pdf_file) as pdf:
                            content = " ".join(page.extract_text() for page in pdf.pages)
                else:
                    logger.info(f"Parsing HTML content from: {url}")
                    soup = BeautifulSoup(response.content, 'html.parser')
                    content = soup.get_text()

            except (requests.exceptions.RequestException, Exception) as e:
                logger.error(f"Could not fetch or parse content from: {url}: {e}")
                return {**paper_info, 'authors': [], 'abstract': 'Fetch/Parse Error'}

            truncated_content = content

            prompt = f"First, determine if the following text is from an academic paper. If it is, output the title, authors, publication date, abstract, and DOI. The authors should be a list of strings, with each string being the full name of an author. Return the information in a JSON object with the keys 'title', 'authors', 'publication_date', 'abstract', and 'doi'. If it is not an academic paper, return the string 'not an academic paper'.\n\nText:{truncated_content}"

            logger.info(f"Running metadata extraction model for: {url}")

            max_retries = 3
            base_delay = 2
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(prompt)
                    break
                except Exception as e:
                    logger.warning(f"Gemini API call failed on attempt {attempt + 1}/{max_retries} for {url}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(base_delay * (2 ** attempt))
                    else:
                        logger.error(f"All {max_retries} Gemini API calls failed for {url}.")
                        return {**paper_info, 'authors': [], 'abstract': 'API Error'}

            logger.info(f"Gemini API Response:\n{response}")

            if "not an academic paper" in response.text.lower():
                logger.info(f"Skipping non-academic paper: {url}")
                return paper_info

            try:
                match = re.search(r'```json\n(.*?)\n```', response.text, re.DOTALL)
                if match:
                    json_text = match.group(1)
                else:
                    json_text = response.text
                metadata = json.loads(json_text)
                paper_info['title'] = metadata.get('title', 'N/A')
                paper_info['authors'] = metadata.get('authors', ['N/A'])
                paper_info['year'] = metadata.get('publication_date', 'N/A')
                paper_info['abstract'] = metadata.get('abstract', 'N/A')
                paper_info['doi'] = metadata.get('doi', 'N/A')
            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"Could not parse JSON from Gemini API response: {e}")
                paper_info['abstract'] = response.text

            return paper_info
        else:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
            }
            try:
                time.sleep(1)
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

                if not paper_info.get('authors'):
                    authors = [meta['content'] for meta in soup.find_all('meta', {'name': 'citation_author'})]
                    if not authors:
                        author_tags = soup.find_all('a', class_=['author', 'authors'])
                        authors = [tag.text for tag in author_tags]
                    paper_info['authors'] = authors or ['N/A']

                if not paper_info.get('abstract'):
                    abstract_tag = soup.find('div', class_=['abstract', 'abstract-content'])
                    abstract = abstract_tag.text.strip() if abstract_tag else 'N/A'
                    if abstract == 'N/A':
                        meta_abstract = soup.find('meta', {'name': ['citation_abstract', 'description']})
                        if meta_abstract:
                            abstract = meta_abstract['content']
                    paper_info['abstract'] = abstract or 'N/A'

                return paper_info

            except requests.exceptions.RequestException as e:
                logger.error(f"Could not fetch or timed out for {url}: {e}")
                return {**paper_info, 'authors': paper_info.get('authors', ['N/A']), 'abstract': 'Fetch Error'}
            except Exception as e:
                logger.error(f"An error occurred during extraction from {url}: {e}")
                return {**paper_info, 'authors': paper_info.get('authors', ['N/A']), 'abstract': 'Extraction Error'}
