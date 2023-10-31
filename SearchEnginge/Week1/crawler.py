import time
import requests
import icecream as ic
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, urlparse


class crawler:

    def __init__(self, start_url):

        self.start_url = start_url
        self.base_netloc = urlparse(self.start_url).netloc
        self.url_stack = [self.start_url]
        self.visited = []
        self.session = requests.Session()
    
    def crawl(self):

        url = self.url_stack.pop()

        if url in self.visited:
            return
        
        
        self.visited.append(url)
        
        response = self.session.get(url)

        if response.status_code == 200 and "text/html" in response.headers["Content-Type"]: # evtl 300 codes 
            soup = bs(response.text, 'html.parser')
            ic.ic(url)
            # Add to index

       
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
    start = time.time()
    webcrawler = crawler(start_url = 'https://www.optikmeyer.de/')
    webcrawler.crawl()
    print(time.time() - start)
