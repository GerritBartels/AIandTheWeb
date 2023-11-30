# Flask Search Engine

This project is a simple search engine built with Flask, Whoosh or a custom index, and a custom web crawler.

## Showcase

![SearchEngineShowcase](https://github.com/GerritBartels/AIandTheWeb/assets/64156238/952c1e69-4d9a-4234-993f-16e557dafd26)

## Features

- **Web Crawling**: The search engine uses a custom-built web crawler to fetch and index web pages. The crawler can be run in parallel using multiple threads for increased performance.
- **Search**: The search engine uses Whoosh, a fast, featureful full-text indexing and searching library or our custom implementation, to index and search the crawled web pages.
- **Web Interface**: The search engine provides a simple yet visually appealing web interface built with Flask. Users can enter their search queries and get the search results displayed in a user-friendly format.

## Usage

1. Clone the repository.
2. Install the required dependencies: `pip install -r requirements.txt`
3. Run the Flask app: `python flask_search_engine.py`

## Configuration

You can configure the search engine by modifying the following variables in `flask_search_engine.py`:

- `START_URL`: The URL where the web crawler starts crawling.
- `INDEX_DIR_NAME`: The directory where the index is stored.
- `LOAD_INDEX_FROM_FILE`: Whether to load the index from file. If set to `False`, the web crawler will start crawling and build the index.
- `NUM_THREADS`: The number of threads used by the web crawler.
- `DEBUG`: Whether to run the Flask app in debug mode.
