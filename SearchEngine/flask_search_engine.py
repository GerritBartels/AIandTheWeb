from time import perf_counter
from flask import Flask, request, render_template, redirect

from custom_index import Index
from crawler_parallel import Crawler


app = Flask(__name__)
index = Index(load_from_file=True)

@app.route("/")
def start():
    return render_template('start.html')

@app.route("/search")
def process_query():
    query = request.args.get('q')

    if not query:
        return redirect("/")

    start_time = perf_counter()
    search_results = index.search(query)
    number_of_results = len(search_results)
    search_time = round(perf_counter() - start_time, 6)

    additional_info = {'number_of_results': number_of_results, 'search_time': search_time}

    return render_template('search_results.html', search_results=search_results, query=query, additional_info=additional_info)


if __name__ == "__main__":

    start_url = 'https://vm009.rz.uos.de/crawl/index.html'
    num_threads = 1

    #webcrawler = Crawler(start_url, index)
    #webcrawler.start_crawling(num_threads)

    #index.build_index()
    
    app.run(debug=True)