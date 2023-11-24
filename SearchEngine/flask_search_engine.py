from time import perf_counter
from flask import Flask, request, render_template, redirect

from custom_index import CustomIndex
from whoosh_index import WhooshIndex

from crawler import Crawler
from parallel_crawler import ParallelCrawler


app = Flask(__name__)
index = CustomIndex(load_from_file=False)


@app.route("/")
def start():
    """Renders the start page of the search engine."""

    return render_template("start.html")


@app.route("/search")
def process_query():
    """Renders the search results page of the search engine."""

    query = request.args.get("q")

    # If no query is given, redirect to start page
    if not query:
        return redirect("/")

    start_time = perf_counter()
    search_results = index.search(query)
    number_of_results = len(search_results)
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


if __name__ == "__main__":
    START_URL = "https://vm009.rz.uos.de/crawl/index.html"
    NUM_THREADS = 1

    webcrawler = ParallelCrawler(START_URL, index)
    webcrawler.start_crawling(NUM_THREADS)

    index.build_index()

    app.run(debug=True)
