import os

from whoosh.qparser import QueryParser
from whoosh.fields import TEXT, ID, Schema
from whoosh.index import create_in, open_dir


class WhooshIndex:
    """Class for building and searching an inverted index based on Whoosh."""

    def __init__(
        self, load_from_file: bool = False, file_name: str = "whoosh_index"
    ) -> None:
        """Initialize the Index.

        Arguments:
            load_from_file (bool): Whether to load the index from a file.
            file_name (str): The name of the file to load the index from and save it to.
        """

        # Create the schema for the index, which specifies the fields that will be indexed and stored.
        self.schema = Schema(
            title=TEXT(stored=True),
            first_paragraph=TEXT(stored=True),
            content=TEXT(),
            url=ID(stored=True),
        )

        if load_from_file:
            self.index = open_dir(dirname="SearchEngine/index", indexname=file_name)

        else:
            if not os.path.exists("SearchEngine/index"):
                os.mkdir("SearchEngine/index")

            self.index = create_in(
                dirname="SearchEngine/index", schema=self.schema, indexname=file_name
            )
            self.writer = self.index.writer()

    def add_to_cache(
        self, title: str, first_paragraph: str, text: str, url: str
    ) -> None:
        """Add the text to the writer, it will preprocess it and add it to the index automatically.

        Arguments:
            title (str): The title of the page.
            first_paragraph (str): The first paragraph of the page.
            text (str): The enitire text of the page used to obtain the word frequencies.
            url (str): The URL of the page.
        """

        self.writer.add_document(
            title=title, first_paragraph=first_paragraph, content=text, url=url
        )

    def build_index(self) -> None:
        """Build the index and save it to a file."""

        self.writer.commit()

    def search(self, query: str) -> list[tuple[str, int, str, str]]:
        """Search the index for the query.

        Arguments:
            query (str): The query to search for.

        Returns:
            result: (list[tuple[str, int, str, str]]): A list of tuples containing the url, 
                dummy count, first paragraph, and title of the pages that match the query.
        """

        result = []
        # Dummy count is needed for compatibility with the custom index.
        dummy_count = 0

        with self.index.searcher() as searcher:
            parsed_query = QueryParser("content", self.index.schema).parse(query)
            results = searcher.search(parsed_query)

            for hit in results:
                result.append(
                    (hit["url"], dummy_count, hit["first_paragraph"], hit["title"])
                )

        return result
