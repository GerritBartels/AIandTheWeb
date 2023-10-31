import time
import threading
import requests
import icecream as ic
from queue import Queue
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse


class Crawler:
    def __init__(self, start_url):
        self.start_url = start_url
        self.base_netloc = urlparse(start_url).netloc
        self.visited = set()
        self.url_queue = Queue()
        self.url_queue.put(start_url)
        self.session = requests.Session()
        self.lock = threading.Lock()

    def crawl(self):
        
        url = self.url_queue.get()

        with self.lock:  # Acquire the lock before accessing self.visited
            if url in self.visited:
                return
            self.visited.add(url)

        response = self.session.get(url)

        if response.status_code == 200 and "text/html" in response.headers["Content-Type"]:
            ic.ic(url)
            soup = bs(response.text, 'html.parser')

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
                thread = threading.Thread(target=self.crawl)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()
            threads = []


if __name__ == '__main__':
    start = time.time()
    start_url = 'https://launchgaia.ni.dfki.de/moodle/'
    num_threads = 1

    crawler = Crawler(start_url)
    crawler.start_crawling(num_threads)
    print(time.time() - start)