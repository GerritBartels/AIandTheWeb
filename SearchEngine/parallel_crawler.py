import requests
import threading
from queue import Queue
from typing import Union
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse

from custom_index import CustomIndex
from whoosh_index import WhooshIndex


class ParallelCrawler:
    """Crawler class for crawling a website and adding its contents to an index. This version uses multithreading."""

    def __init__(self, start_url: str, index: Union[CustomIndex, WhooshIndex]) -> None:
        """Initialize the Crawler.

        Arguments:
            start_url (str): The url of the website to crawl.
            index (Union[Index, WhooshIndex]): The index to add the crawled contents to.
        """
        self.start_url = start_url
        self.base_netloc = urlparse(start_url).netloc
        self.visited: set[str] = set()
        self.url_queue: Queue[str] = Queue()
        self.url_queue.put(start_url)
        self.session = requests.Session()
        self.lock = threading.Lock()
        self.index = index

    def _crawl(self) -> None:
        """Crawl the website and add its contents to the index, if the website hasn't been visited yet.
        It gathers all links on the website and adds them to the url stack.
        """

        url = self.url_queue.get()

        # Check if the url has already been visited in a thread-safe manner
        with self.lock:
            if url in self.visited:
                return
            self.visited.add(url)

        response = self.session.get(url)

        # Check if the response is a valid html page
        if (
            response.status_code == 200
            and "text/html" in response.headers["Content-Type"]
        ):
            soup = bs(response.text, "html.parser")

            title = soup.title.string if soup.title else ""
            # Take the first 200 characters as preview text
            first_paragraph = (
                soup.find("p").get_text()[:200] + "..." if soup.find("p") else ""
            )
            text = soup.get_text() if soup.get_text() else ""

            # Convert elements to strings to avoid pickling errors
            self.index.add_to_cache(
                str(title), str(first_paragraph), str(text), str(url)
            )

            # Gather all available links on the website
            for link in soup.find_all("a"):
                new_url = link.get("href")
                complete_new_url = urljoin(self.start_url, new_url)

                if urlparse(complete_new_url).netloc != self.base_netloc:
                    continue

                self.url_queue.put(complete_new_url)

    def start_crawling(self, num_threads: int = 1) -> None:
        """Start crawling the website with the specified number of threads.
        As long as there are urls in the url queue, each thread will crawl a url.
        """

        threads = []

        while not self.url_queue.empty():
            for _ in range(num_threads):
                if self.url_queue.empty():
                    break
                thread = threading.Thread(target=self._crawl)
                threads.append(thread)
                thread.start()

            # Wait for all threads to finish before starting the next batch
            for thread in threads:
                thread.join()
            threads = []
