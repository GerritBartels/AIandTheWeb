from flask import Flask, request, render_template

from custom_index import Index
from crawler_parallel import Crawler
import icecream as ic


app = Flask(__name__)
index = Index()

@app.route("/")
def start():
    return render_template('start.html')

@app.route("/search")
def process_query(): # what if site is visited without query parameter q?
    query = request.args["q"]

    search_results = index.search(query)
    ic.ic(search_results)

    return render_template('search_results.html', search_results=search_results, query=query)


if __name__ == "__main__":

    start_url = 'https://vm009.rz.uos.de/crawl/index.html'
    num_threads = 1

    webcrawler = Crawler(start_url, index)
    webcrawler.start_crawling(num_threads)

    index.build_index()
    
    app.run(debug=True)