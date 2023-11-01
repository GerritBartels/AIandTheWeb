import nltk
import itertools
from nltk import word_tokenize
from collections import Counter
from nltk.corpus import stopwords

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

    def add_to_cache(self, text, url):

        preprocessed_text = self._preprocess(text)
        counted_words = Counter(preprocessed_text)
        self.cache.append((counted_words, url))

    def build_index(self):

        for counted_words, url in self.cache:
            for word, count in counted_words.items():
                if word not in self.index:
                    self.index[word] = []

                self.index[word].append((url, count))

    def search(self, query):

        preprocessed_query = set(self._preprocess(query))

        search_hits = [self.index[word] for word in preprocessed_query if word in self.index]

        # Flatten the list
        flattened_data = [item for sublist in search_hits for item in sublist]

        # Sort the data by URL
        sorted_data = sorted(flattened_data, key=lambda x: x[0])
        
        # Group by URL and sum up the counts
        grouped_data = [(url, sum(count for _, count in group)) for url, group in itertools.groupby(sorted_data, key=lambda x: x[0])]
    
        # Sort the data by count
        sorted_data = sorted(grouped_data, key=lambda x: x[1], reverse=True)

        return sorted_data


