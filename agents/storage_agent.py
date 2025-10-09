import json
from .base_agent import BaseAgent

class StorageAgent(BaseAgent):
    def __init__(self, filepath='research_digest.json'):
        super().__init__()
        self.desires = {'save_metadata'}
        self.beliefs['filepath'] = filepath
        self.processed_data_count = 0

    def formulate_intentions(self, blackboard):
        if len(blackboard.get("extracted_data", [])) > self.processed_data_count:
            self.beliefs['metadata_list'] = blackboard["extracted_data"]
            self.intentions = [lambda: self.save_to_json(blackboard)]
        else:
            self.intentions = []

    def save_to_json(self, blackboard):
        filepath = self.beliefs['filepath']
        metadata_list = self.beliefs['metadata_list']

        if not metadata_list:
            print("no metadata to save.")
            return

        print(f"saving {len(metadata_list)} items to {filepath}...")

        # we save the data in a structured format that is easy to parse and read
        harvard_style_references = []
        for paper in metadata_list:
            authors = paper.get('authors', [])
            year = paper.get('year', 'N/A')
            title = paper.get('title', 'N/A')
            source = paper.get('source', 'N/A')
            venue = paper.get('venue', 'N/A')
            doi = paper.get('doi', 'N/A')
            url = paper.get('url', 'N/A')
            abstract = paper.get('abstract', 'N/A')

            harvard_style_references.append({
                "authors": authors,
                "year": year,
                "title": title,
                "source": source,
                "venue": venue,
                "doi": doi,
                "url": url,
                "abstract": abstract
            })

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(harvard_style_references, f, indent=4, ensure_ascii=False)
            self.processed_data_count = len(metadata_list)
            print("save successful.")
            blackboard["storage_complete"] = True
        except IOError as e:
            print(f"error saving to file {filepath}: {e}")
            blackboard["status"] = "error"
