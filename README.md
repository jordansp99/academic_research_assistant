# Academic Research Assistant

This is a simple application that helps with academic research by searching for papers from various sources and extracting metadata from them.

## Setup

1.  **Install Dependencies:** Install the required Python packages using pip:

    ```bash
    pip install -r requirements.txt
    ```

2.  **Gemini API Key:** This project uses the Gemini API to extract metadata from web pages. You will need a Gemini API key to use this feature.

    *   **Get your API key:** You can get a Gemini API key from the [Google AI Studio](https://aistudio.google.com/app/apikey).
    *   **Create a .env file:** Create a `.env` file in the root of the project by copying the `.env.example` file:

        ```bash
        cp .env.example .env
        ```

    *   **Add your API key to the .env file:** Open the `.env` file and replace `"YOUR_API_KEY"` with your actual Gemini API key.

3.  **Semantic Scholar API Key (Optional):** This project can use the Semantic Scholar API to fetch paper details. While not required, providing an API key is recommended for higher rate limits.

    *   **Get your API key:** You can request a Semantic Scholar API key from their official website.
    *   **Add your API key to the .env file:** Open the `.env` file and add the following line, replacing `"YOUR_API_KEY"` with your actual Semantic Scholar API key:
        ```
        S2_API_KEY="YOUR_API_KEY"
        ```


## Usage

To run the application, execute the following command in your terminal:

```bash
python gui.py
```
