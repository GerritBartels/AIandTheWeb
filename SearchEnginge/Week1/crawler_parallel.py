import time
import threading
import requests
import icecream as ic
from queue import Queue
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse

from index import Index


class Crawler:
    def __init__(self, start_url, index):
        self.start_url = start_url
        self.base_netloc = urlparse(start_url).netloc
        self.visited = set()
        self.url_queue = Queue()
        self.url_queue.put(start_url)
        self.session = requests.Session()
        self.lock = threading.Lock()
        self.index = index

    def _crawl(self):
        
        url = self.url_queue.get()

        with self.lock:  # Acquire the lock before accessing self.visited
            if url in self.visited:
                return
            self.visited.add(url)

        response = self.session.get(url)

        if response.status_code == 200 and "text/html" in response.headers["Content-Type"]:
            soup = bs(response.text, 'html.parser')
            text = soup.get_text()
            self.index.add_to_cache(text, url)

            for link in soup.find_all('a'):
                new_url = link.get('href')
                complete_new_url = urljoin(self.start_url, new_url)

                if urlparse(complete_new_url).netloc != self.base_netloc:
                    continue

                self.url_queue.put(complete_new_url)

    def start_crawling(self, num_threads):
        threads = []

        while not self.url_queue.empty():
            for _ in range(num_threads):
                if self.url_queue.empty():
                    break
                thread = threading.Thread(target=self._crawl)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()
            threads = []


if __name__ == '__main__':
    start_time = time.time()
    start_url = 'https://vm009.rz.uos.de/crawl/index.html'
    num_threads = 1
    index = Index()

    webcrawler = Crawler(start_url, index)
    webcrawler.start_crawling(num_threads)

    index.build_index()
    search_results = index.search('unicorn platypus')

    ic.ic(search_results)
    elapsed_time = round(time.time() - start_time, 4)
    print(f"Elapsed time: {elapsed_time} seconds")