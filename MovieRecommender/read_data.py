import csv
import sys
import datetime
import flask_user
import flask_sqlalchemy
from sqlalchemy.exc import IntegrityError
from models import User, Movie, MovieGenre, MovieLinks, MovieTags, MovieRatings


def check_and_read_data(db: flask_sqlalchemy.extension.SQLAlchemy, user_manager: flask_user.user_manager.UserManager) -> None:
    """Reads data from movies, links, tags and ratings csv files and stores them in the database.
    
    Arguments:
        db (flask_sqlalchemy.extension.SQLAlchemy): The SQLAlchemy database object.
        user_manager (flask_user.user_manager.UserManager): The UserManager object.
    """

    # Check if we have movies in the database,
    # read data if database is empty
    if Movie.query.count() == 0:
        # Read movies from csv
        with open('data/movies.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
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
                        # genres is a list of genres
                        genres = row[2].split('|')  

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
                    print('\r' + str(count), " movies read", end="")

        print("\nFinished reading in movies \n")


    if MovieLinks.query.count() == 0:
        with open('data/links.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0

            for row in reader:
                if count > 0:
                    try:
                        movie_id = row[0]
                        imdb_id = row[1]
                        tmdb_id = row[2]
                        movie_link = MovieLinks(movie_id=movie_id, imdb_id=imdb_id, tmdb_id=tmdb_id)
                        db.session.add(movie_link)
                        db.session.commit()

                    except IntegrityError:
                        print("\nIgnoring duplicate movie link: " + movie_id)
                        db.session.rollback()
                        pass

                count += 1
                if count % 100 == 0:
                    print('\r' + str(count), " movie links read", end="")

        print("\nFinished reading in links \n")


    if MovieTags.query.count() == 0:
        with open('data/tags.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0

            for row in reader:
                if count > 0:
                    try:
                        user_id = row[0]
                        
                        if User.query.filter_by(id=user_id).count() == 0:
                            username = f"User{user_id}"
                            user = User(id=user_id, username=username, password=user_manager.hash_password(username))
                            db.session.add(user)

                        movie_id = row[1]
                        tag = row[2]
                        timestamp = row[3]
                        movie_tag = MovieTags(user_id=user_id, movie_id=movie_id, tag=tag, timestamp=datetime.date.fromtimestamp(int(timestamp)))
                        db.session.add(movie_tag)
                        db.session.commit()

                    except IntegrityError:
                        print("\nIntegrity error for tag: " + tag + " for movie: " + movie_id + " by user: " + user_id)
                        db.session.rollback()
                        pass

                count += 1
                if count % 100 == 0:
                    print('\r' + str(count), " movie tags read", end="")

        print("\nFinished reading in tags \n")


    if MovieRatings.query.count() == 0:
        with open('data/ratings.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0

            for row in reader:
                if count > 0:
                    try:
                        user_id = row[0]

                        if User.query.filter_by(id=user_id).count() == 0:
                            username = f"User{user_id}"
                            user = User(id=user_id, username=username, password=user_manager.hash_password(username))
                            db.session.add(user)

                        movie_id = row[1]
                        rating = row[2]
                        timestamp = row[3]
                        movie_rating = MovieRatings(user_id=user_id, movie_id=movie_id, rating=rating, timestamp=datetime.date.fromtimestamp(int(timestamp)))
                        db.session.add(movie_rating)

                        # Commit every 2000 rows
                        if count % 2000 == 0:
                            db.session.commit()
                            print('\r' + str(count), " movie ratings read", end="")

                    except IntegrityError:
                        db.session.rollback()
                        print("\nIntegrity error for rating: " + rating + " for movie: " + movie_id + " by user: " + user_id)
                        continue

                count += 1

            # Commit remaining rows
            db.session.commit()

        print("\nFinished reading in ratings \n")