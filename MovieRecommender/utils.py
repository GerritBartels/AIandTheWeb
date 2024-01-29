import csv
import requests
import datetime
import threading
import flask_user
import numpy as np
import flask_sqlalchemy
from collections import Counter
from sqlalchemy.exc import IntegrityError
from models import User, Movie, MovieGenre, MovieLinks, MovieTags, MovieRatings


def check_and_read_data(
    db: flask_sqlalchemy.extension.SQLAlchemy,
    user_manager: flask_user.user_manager.UserManager,
) -> None:
    """Reads data from movies, links, tags and ratings csv files and stores them in the database.

    Arguments:
        db (flask_sqlalchemy.extension.SQLAlchemy): The SQLAlchemy database object.
        user_manager (flask_user.user_manager.UserManager): The UserManager object.
    """

    # Check if we have movies in the database,
    # read data if database is empty
    if Movie.query.count() == 0:
        # Read movies from csv
        with open("data/movies.csv", newline="", encoding="utf8") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            count = 0

            for row in reader:
                if count > 0:
                    try:
                        id = row[0]
                        title = row[1]
                        # Year is always part of the title
                        year = title[-5:-1]
                        movie = Movie(id=id, title=title, year=year)
                        db.session.add(movie)
                        # Genres is a list of genres
                        genres = row[2].split("|")

                        for genre in genres:
                            movie_genre = MovieGenre(movie_id=id, genre=genre)
                            db.session.add(movie_genre)

                        db.session.commit()

                    except IntegrityError:
                        print("\nIgnoring duplicate movie: " + title)
                        db.session.rollback()
                        pass

                count += 1
                if count % 100 == 0:
                    print("\r" + str(count), " movies read", end="")

        print("\nFinished reading in movies \n")

    if MovieLinks.query.count() == 0:
        with open("data/links.csv", newline="", encoding="utf8") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            count = 0

            for row in reader:
                if count > 0:
                    try:
                        movie_id = row[0]
                        imdb_id = row[1]
                        tmdb_id = row[2]
                        movie_link = MovieLinks(
                            movie_id=movie_id, imdb_id=imdb_id, tmdb_id=tmdb_id
                        )
                        db.session.add(movie_link)
                        db.session.commit()

                    except IntegrityError:
                        print("\nIgnoring duplicate movie link: " + movie_id)
                        db.session.rollback()
                        pass

                count += 1
                if count % 100 == 0:
                    print("\r" + str(count), " movie links read", end="")

        print("\nFinished reading in links \n")

    if MovieTags.query.count() == 0:
        with open("data/tags.csv", newline="", encoding="utf8") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            count = 0

            for row in reader:
                if count > 0:
                    try:
                        user_id = row[0]
                        username = f"User{user_id}"
                        query = User.query.filter_by(username=username)

                        # Create a new user if the user doesn't exist in the database
                        if query.count() == 0:
                            user = User(
                                username=username,
                                password=user_manager.hash_password(username),
                            )
                            db.session.add(user)
                            db.session.commit()
                            user_id = user.id
                        else:
                            user_id = query.first().id

                        movie_id = row[1]
                        tag = row[2]
                        timestamp = row[3]
                        movie_tag = MovieTags(
                            user_id=user_id,
                            movie_id=movie_id,
                            tag=tag,
                            timestamp=datetime.date.fromtimestamp(int(timestamp)),
                        )
                        db.session.add(movie_tag)
                        db.session.commit()

                    except IntegrityError:
                        print(
                            "\nIntegrity error for tag: "
                            + tag
                            + " for movie: "
                            + movie_id
                            + " by user: "
                            + user_id
                        )
                        db.session.rollback()
                        pass

                count += 1
                if count % 100 == 0:
                    print("\r" + str(count), " movie tags read", end="")

        print("\nFinished reading in tags \n")

    dict_for_avg: dict[str, list] = {}

    if MovieRatings.query.count() == 0:
        with open("data/ratings.csv", newline="", encoding="utf8") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            count = 0

            for row in reader:
                if count > 0:
                    try:
                        user_id = row[0]
                        username = f"User{user_id}"
                        query = User.query.filter_by(username=username)

                        # Create a new user if the user doesn't exist in the database
                        if query.count() == 0:
                            user = User(
                                username=username,
                                password=user_manager.hash_password(username),
                            )
                            db.session.add(user)
                            db.session.commit()
                            user_id = user.id
                        else:
                            user_id = query.first().id

                        movie_id = row[1]
                        rating = row[2]
                        timestamp = row[3]
                        movie_rating = MovieRatings(
                            user_id=user_id,
                            movie_id=movie_id,
                            rating=rating,
                            timestamp=datetime.date.fromtimestamp(int(timestamp)),
                        )
                        db.session.add(movie_rating)

                        # Sum ratings for each movie and count the number of ratings
                        if movie_id in dict_for_avg:
                            dict_for_avg[movie_id][0] += float(rating)
                            dict_for_avg[movie_id][1] += 1
                        else:
                            dict_for_avg[movie_id] = [float(rating), 1]

                        # Commit every 2000 rows
                        if count % 2000 == 0:
                            db.session.commit()
                            print("\r" + str(count), " movie ratings read", end="")

                    except IntegrityError:
                        db.session.rollback()
                        print(
                            "\nIntegrity error for rating: "
                            + rating
                            + " for movie: "
                            + movie_id
                            + " by user: "
                            + user_id
                        )
                        continue

                count += 1

            # Commit remaining rows
            db.session.commit()

        print("\nFinished reading in ratings \n")


    print("Updating average ratings...")

    # Update average ratings for each movie
    for movie_id, (rating_sum, rating_count) in dict_for_avg.items():
        movie = Movie.query.filter_by(id=movie_id).first()
        if movie is not None:
            movie.avg_rating = round(rating_sum / rating_count, 4)
            movie.num_ratings = rating_count
    db.session.commit()
    
    print("Finished updating average ratings \n")


def fetch_movie_info(movie_info_url: str, movie_id: int, session: requests.Session, movie_info_dict: dict):
    """Fetches movie plot description from the OMDB API. This function is used in a thread.
    
    Arguments:
        movie_info_url (str): The movie info URL.
        movie_id (int): The movie ID.
        session (requests.Session): The requests session.
        movie_info_dict (dict): The dictionary to store the movie info.
    """
    movie_info_dict[movie_id] = session.get(movie_info_url).json()


def get_movie_metadata(
    db: flask_sqlalchemy.extension.SQLAlchemy,
    movies: list,
    current_user: User,
    get_user_ratings: bool = True,
    get_movie_plot: bool = True,
) -> (dict, dict, dict):
    """Gets movie metadata from the database, i.e., tags, average ratings, and user ratings.

    Arguments:
        db (flask_sqlalchemy.extension.SQLAlchemy): The SQLAlchemy database object.
        movies (list): A list of Movie objects.
        current_user (User): The current user.
        get_user_ratings (bool): Whether to get ratings for the current user.
        get_movie_plot (bool): Whether to get movie plot descriptions.

    Returns:
        movie_tags (dict): A dictionary of movie tags.
        average_ratings (dict): A dictionary of average ratings.
        user_ratings (dict): A dictionary of user ratings.
        movie_plot_dict (dict): A dictionary of movie plot descriptions.
    """

    movie_tags = {}
    average_ratings = {}
    user_ratings = {}
    movie_plot_dict = {}

    # Fetch all ratings for all movies in one go
    all_ratings = (
        db.session.query(
            MovieRatings.movie_id,
            db.func.avg(MovieRatings.rating),
            db.func.count(MovieRatings.movie_id),
        )
        .group_by(MovieRatings.movie_id)
        .all()
    )

    # Convert the result into a dictionary for easy access
    all_ratings_dict = {movie_id: (avg, count) for movie_id, avg, count in all_ratings}

    if get_user_ratings:
        # Fetch all user ratings for all movies in one go
        all_user_ratings = MovieRatings.query.filter_by(user_id=current_user.id).all()

        # Convert the result into a dictionary for easy access
        all_user_ratings_dict = {
            rating.movie_id: rating.rating for rating in all_user_ratings
        }

    # Create a list to hold all the threads 
    # and a session for each thread
    if get_movie_plot:
        request_session = requests.Session()
        threads = []

    for movie in movies:
        # Get movie tags for each movie, sort them by tag count first and then alphabetically
        if movie.tags:
            tag_counts = Counter([tag.tag.lower() for tag in movie.tags])
            sorted_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))
            sorted_tags = [key.title() for key in dict(sorted_tags).keys()]
            movie_tags[movie.id] = sorted_tags

        # Get average rating for each movie
        if movie.id in all_ratings_dict:
            avg, count = all_ratings_dict[movie.id]
            average_ratings[movie.id] = (round(avg, 1), count)
        else:
            average_ratings[movie.id] = (0.0, 0)

        # Get rating for each movie by the logged in user
        if get_user_ratings:
            if movie.id in all_user_ratings_dict:
                user_ratings[movie.id] = all_user_ratings_dict[movie.id]

        # Get movie plot description for each movie
        if get_movie_plot:
            if movie.links[0].imdb_id:
                movie_info_url = f"http://www.omdbapi.com/?i=tt{movie.links[0].imdb_id}&apikey="
                thread = threading.Thread(target=fetch_movie_info, args=(movie_info_url, movie.id, request_session, movie_plot_dict))
                threads.append(thread)

    if get_movie_plot:
        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

    return movie_tags, average_ratings, user_ratings, movie_plot_dict


def softmax(logits) -> np.array:
    """Computes softmax activations.

    Arguments:
        logits (np.array): The logits.

    Returns:
        np.array: The softmax activations.
    """

    exp = np.exp(logits)
    return exp / np.sum(exp)


class CustomPagination:
    """Custom pagination class. Needed because the default pagination class
    doesn't support the lists, which are used on the movies search page.
    """

    def __init__(self, items: list, page: int, per_page: int, total: int) -> None:
        """Initializes the CustomPagination class.
        
        Arguments:
            items (list): The items to paginate.
            page (int): The current page.
            per_page (int): The number of items per page.
            total (int): The total number of items.
        """
        
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total

    def __iter__(self) -> iter:
        """Iterates over the items.
        
        Returns:
            iter: The iterator.
        """

        return iter(self.items)

    def iter_pages(self, left_edge: int=2, left_current: int=2, right_current: int=5, right_edge: int=2) -> int:
        """Iterates over the pages. Needed for the pagination buttons. 

        Arguments:
            left_edge (int): The number of pages on the left edge.
            left_current (int): The number of pages on the left side of the current page.
            right_current (int): The number of pages on the right side of the current page.
            right_edge (int): The number of pages on the right edge.

        Yields:
            int: The next page.
        """

        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

    @property
    def pages(self) -> int:
        """The total number of pages.
        
        Returns:
            int: The total number of pages.
        """

        return max(0, self.total - 1) // self.per_page + 1
