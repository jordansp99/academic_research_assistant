## Academic Research Assistant

## Overview

The Academic Research Assistant is a desktop application designed to simplify the process of finding and collecting academic papers. It offers a user-friendly interface for searching across various sources, extracting crucial metadata, and storing the results for later reference.

## Features

- **Multi-source Search:** Search for papers across multiple academic databases and search engines, including:
    - arXiv
    - Semantic Scholar
    - PubMed
    - DuckDuckGo (for general web searches)
- **Metadata Extraction:** Automatically extracts key information from the search results, such as the title, authors, abstract, DOI, and publication year.
- **PDF Parsing:** Capable of parsing PDF files to extract metadata, even when it is not readily available on the web page.
- **Advanced Search Options:** Customise the number of papers to fetch from each source.
- **Persistent Settings:** Your advanced search settings are saved locally, meaning you won't need to reconfigure them every time you open the application.
- **Save to JSON:** Store the collected paper information in a structured JSON file for straightforward integration with other tools.

## How it Works

The application employs an agent-based architecture, with different agents handling specific tasks:

- **Search Agent:** Responsible for querying the various data sources in parallel.
- **Extraction Agent:** Responsible for fetching the content from the paper URLs and extracting the metadata. It utilises the Gemini API for advanced metadata extraction from unstructured text.
- **Storage Agent:** Responsible for saving the collected data to a JSON file.

These agents communicate via a central "blackboard," which is a shared data structure that holds the application's current state.

## File Structure

- `gui.py`: The main entry point for the application. It contains the code for the user interface, built with PyQt6.
- `agents/`: This directory houses the various agents used in the application.
    - `base_agent.py`: An abstract base class for all agents.
    - `search_agent.py`: The agent responsible for searching for papers.
    - `extraction_agent.py`: The agent responsible for extracting metadata.
    - `storage_agent.py`: The agent responsible for saving the data.
- `logging_config.py`: Configures the logging for the application.
- `utils.py`: Contains utility functions used by the agents.
- `requirements.txt`: A list of the Python dependencies required to run the application.
- `.env.example`: An example file for the environment variables.
- `README.md`: This file.

## Setup and Configuration

### 1. Installation

Install the necessary Python packages via pip:

```bash
pip install -r requirements.txt
```

### 2. API Keys

#### Gemini API Key

This project relies on the Gemini API to extract metadata from web pages. A Gemini API key is required to use this feature.

- **Obtain your API key:** You can get a Gemini API key from the [Google AI Studio](https://aistudio.google.com/app/apikey).
- **Create a .env file:** Create a `.env` file in the root directory of the project by copying the `.env.example` file:

    ```bash
    cp .env.example .env
    ```

- **Add your API key to the .env file:** Open the `.env` file and replace `"YOUR_API_KEY"` with your actual Gemini API key.

#### Semantic Scholar API Key (Optional)

This project can utilise the Semantic Scholar API to fetch paper details. While not mandatory, supplying an API key is highly recommended to benefit from higher rate limits.

- **Obtain your API key:** You can request a Semantic Scholar API key from their official website.
- **Add your API key to the .env file:** Open the `.env` file and add the following line, replacing `"YOUR_API_KEY"` with your actual Semantic Scholar API key:
    ```
    S2_API_KEY="YOUR_API_KEY"
    ```

### 3. Advanced Settings

You can configure the number of papers to fetch from each source by clicking the "Advanced Settings" button within the application.

## Usage

To run the application, execute the following command in your terminal:

```bash
python gui.py
```
