from pathlib import Path
__location__ = Path(__file__).parent.resolve()

import sys
sys.path.insert(1, __location__.__str__())

import os
os.chdir(__location__)

import traceback
from time import perf_counter
from flask import Flask, request, render_template, redirect, url_for

from custom_index import CustomIndex
from whoosh_index import WhooshIndex

from crawler import Crawler
from parallel_crawler import ParallelCrawler


app = Flask(__name__)


@app.route("/")
def start():
    """Renders the start page of the search engine."""

    return render_template("start.html")


@app.route("/search")
def search():
    """Renders the search results page of the search engine."""

    query = request.args.get("q")

    # If no query is given, redirect to start page
    if not query:
        return redirect(url_for('start'))

    start_time = perf_counter()
    search_results = index.search(query)
    number_of_results = len(search_results[1])
    search_time = round(perf_counter() - start_time, 6)

    additional_info = {
        "number_of_results": number_of_results,
        "search_time": search_time,
    }

    return render_template(
        "search_results.html",
        search_results=search_results,
        query=query,
        additional_info=additional_info,
    )


START_URL = "https://vm009.rz.uos.de/crawl/index.html"
INDEX_DIR_NAME = "whoosh_vm009"
LOAD_INDEX_FROM_FILE = False

NUM_THREADS = 4
DEBUG = False


index = WhooshIndex(load_from_file=LOAD_INDEX_FROM_FILE, dir_name=INDEX_DIR_NAME)

if not LOAD_INDEX_FROM_FILE:
    webcrawler = ParallelCrawler(START_URL, index)
    webcrawler.start_crawling(NUM_THREADS)

    index.build_index()

app.run(debug=DEBUG)
