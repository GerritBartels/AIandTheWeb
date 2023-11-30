import os

from whoosh.qparser import QueryParser, OrGroup
from whoosh.writing import BufferedWriter
from whoosh.fields import TEXT, ID, Schema
from whoosh.index import create_in, open_dir
from whoosh.highlight import SentenceFragmenter, HtmlFormatter


class WhooshIndex:
    """Class for building and searching an inverted index based on Whoosh."""

    def __init__(
        self, load_from_file: bool = False, dir_name: str = "whoosh_index"
    ) -> None:
        """Initialize the Index.

        Arguments:
            load_from_file (bool): Whether to load the index from a file.
            dir_name (str): The name of the dir to load the index from and save it to.
        """

        # Create the schema for the index, which specifies the fields that will be indexed and stored.
        self.schema = Schema(
            title=TEXT(stored=True),
            first_paragraph=TEXT(stored=True),
            content=TEXT(stored=True),
            url=ID(stored=True),
        )

        self.search_fragmenter = SentenceFragmenter(charlimit=250)
        self.highlight_formatter = HtmlFormatter(classname="change")

        if load_from_file:
            self.index = open_dir(dirname=f"index/{dir_name}", indexname="index")

        else:
            if not os.path.exists(f"index/{dir_name}"):
                os.makedirs(f"index/{dir_name}")

            self.index = create_in(
                dirname=f"index/{dir_name}", schema=self.schema, indexname="index"
            )
            self.writer = BufferedWriter(self.index, period=2, limit=2)

    def add_to_cache(
        self, title: str, first_paragraph: str, text: str, url: str
    ) -> None:
        """Add the text to the writer, it will preprocess it and add it to the index automatically.

        Arguments:
            title (str): The title of the page.
            first_paragraph (str): The first paragraph of the page.
            text (str): The entire text of the page used to obtain the word frequencies.
            url (str): The URL of the page.
        """

        self.writer.add_document(
            title=title, first_paragraph=first_paragraph, content=text, url=url
        )

    def build_index(self) -> None:
        """Build the index and save it to a file."""

        self.writer.commit()
        self.writer.close()

    def search(self, query: str) -> list[tuple[str, int, str, str]]:
        """Search the index for the query. If the query is misspelled, the corrected query is returned as well.
        The queried words are highlighted in the results.

        Arguments:
            query (str): The query to search for.

        Returns:
            result: (list[tuple[str, int, str, str]]): A list of tuples containing the url,
                dummy count, first paragraph, and title of the pages that match the query.
        """

        result = [[], []]
        # Dummy count is needed for compatibility with the custom index.
        dummy_count = 0

        with self.index.searcher() as searcher:
            parsed_query = searcher.correct_query(
                QueryParser(
                    "content", self.index.schema, group=OrGroup.factory(0.9)
                ).parse(query),
                query,
            )
            results = searcher.search(parsed_query.query)
            results.fragmenter = self.search_fragmenter

            if parsed_query.string != query:
                result[0] = (
                    parsed_query.format_string(self.highlight_formatter),
                    parsed_query.string,
                )

            for hit in results:
                result[1].append(
                    (hit["url"], dummy_count, hit.highlights("content"), hit["title"])
                )

        return result
