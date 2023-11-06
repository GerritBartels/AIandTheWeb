import time
import requests
import icecream as ic
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse

from custom_index import Index


class Crawler:

    def __init__(self, start_url, index):

        self.start_url = start_url
        self.base_netloc = urlparse(self.start_url).netloc
        self.url_stack = [self.start_url]
        self.visited = []
        self.session = requests.Session()
        self.index = index
    
    def crawl(self):

        url = self.url_stack.pop()

        if url in self.visited:
            return
        
        
        self.visited.append(url)
        
        response = self.session.get(url)

        if response.status_code == 200 and "text/html" in response.headers["Content-Type"]: # evtl 300 codes 
            soup = bs(response.text, 'html.parser')
            text = soup.get_text()
            self.index.add_to_cache(text, url)

       
            for link in soup.find_all('a'):
                new_url = link.get('href')
                complete_new_url = urljoin(self.start_url, new_url)
                
                if urlparse(complete_new_url).netloc != self.base_netloc:
                    return
                
                self.url_stack.append(complete_new_url)
                self.crawl() 
        
        else:
            return


if __name__ == '__main__':
    start_time = time.time()
    start_url = 'https://vm009.rz.uos.de/crawl/index.html'
    index = Index()

    webcrawler = Crawler(start_url, index)
    webcrawler.crawl()

    index.build_index()
    search_results = index.search('unicorn platypus')
    
    ic.ic(search_results)
    elapsed_time = round(time.time() - start_time, 4)
    print(f"Elapsed time: {elapsed_time} seconds")
