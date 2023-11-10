import os

from whoosh.qparser import QueryParser
from whoosh.index import create_in, open_dir
from whoosh.fields import TEXT, ID, Schema


class Index():

    def __init__(self, load_from_file=False):

        self.schema = Schema(title=TEXT(stored=True), first_paragraph=TEXT(stored=True), content=TEXT(), url=ID(stored=True))

        if load_from_file:
            self.index = open_dir(dirname="SearchEngine/index", indexname="whoosh_index")

        else:
            if not os.path.exists("SearchEngine/index"):
                os.mkdir("SearchEngine/index")
                
            self.index = create_in(dirname="SearchEngine/index", schema=self.schema, indexname="whoosh_index")
            self.writer = self.index.writer()

    def add_to_cache(self, title, first_paragraph, text, url):

        self.writer.add_document(title=title, first_paragraph=first_paragraph, content=text, url=url)

    def build_index(self):

        self.writer.commit()

    def search(self, query):

        result = []
        dummy_count = 0

        with self.index.searcher() as searcher:
            parsed_query = QueryParser("content", self.index.schema).parse(query)
            results = searcher.search(parsed_query)
            
            for hit in results:
                result.append((hit['url'], dummy_count, hit['first_paragraph'], hit['title']))

        return result
