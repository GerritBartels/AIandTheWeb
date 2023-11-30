import time
import requests
import icecream as ic
from typing import Union
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse

from custom_index import CustomIndex
from whoosh_index import WhooshIndex


class Crawler:
    """Crawler class for crawling a website and adding its contents to an index."""

    def __init__(self, start_url: str, index: Union[CustomIndex, WhooshIndex]) -> None:
        """Initialize the Crawler.

        Arguments:
            start_url (str): The url of the website to crawl.
            index (Union[Index, WhooshIndex]): The index to add the crawled contents to.
        """

        self.start_url = start_url
        self.base_netloc = urlparse(
            self.start_url
        ).netloc  # Crawler only crawls pages from the base netloc domain
        self.url_stack = [self.start_url]
        self.visited: list[str] = []
        self.session = requests.Session()
        self.index = index

    def crawl(self) -> None:
        """Crawl the website and add its contents to the index, if the website hasn't been visited yet.
        It gathers all links on the website and adds them to the url stack.
        """

        url = self.url_stack.pop()

        if url in self.visited:
            return

        self.visited.append(url)

        response = self.session.get(url)

        # Check if the response is a valid html page
        if (
            response.status_code == 200
            and "text/html" in response.headers["Content-Type"]
        ):  # evtl 300 codes
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
                    return

                self.url_stack.append(complete_new_url)
                self.crawl()

        else:
            return
