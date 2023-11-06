import nltk
import itertools
from nltk import word_tokenize
from collections import Counter
from nltk.corpus import stopwords

import icecream as ic

nltk.download('stopwords')


class Index():

    def __init__(self):

        self.cache = []
        self.index = {}
        self.stop_words = set(stopwords.words('english'))

    def _preprocess(self, text):

        text = word_tokenize(text.lower())
        text = [word for word in text if word not in self.stop_words and word.isalnum()]

        return text

    def add_to_cache(self, title, first_paragraph, text, url):

        preprocessed_text = self._preprocess(text)
        counted_words = Counter(preprocessed_text)
        self.cache.append((counted_words, url, first_paragraph, title))

    def build_index(self):

        for counted_words, url, first_paragraph, title in self.cache:
            for word, count in counted_words.items():
                if word not in self.index:
                    self.index[word] = []

                self.index[word].append((url, count, first_paragraph, title))

    def search(self, query):

        preprocessed_query = set(self._preprocess(query))

        # Get search hits
        search_hits = []
        for word in preprocessed_query:
            if word in self.index:
                search_hits.extend(self.index[word])

        # Sort and group data by URL
        search_hits.sort(key=lambda x: x[0])
        grouped_data = itertools.groupby(search_hits, key=lambda x: x[0])

        # Create result list with URL, sum of counts, and sets of first_paragraph and title
        result = []
        for url, group in grouped_data:
            group_list = list(group)
            total_count = sum(item[1] for item in group_list)
            first_paragraph = next(iter({item[2] for item in group_list}), 'Preview unavailable')
            title = next(iter({item[3] for item in group_list}), 'Untitled')
            result.append((url, total_count, first_paragraph, title))

        # Sort the result by count
        result.sort(key=lambda x: x[1], reverse=True)

        return result
