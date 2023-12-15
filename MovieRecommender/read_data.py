import csv
import datetime
from sqlalchemy.exc import IntegrityError
from models import Movie, MovieGenre, MovieLinks, MovieTags, User


def check_and_read_data(db, user_manager):
    # check if we have movies in the database
    # read data if database is empty
    if Movie.query.count() == 0:
        # read movies from csv
        with open('data/movies.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        id = row[0]
                        title = row[1]
                        year = title[-5:-1]
                        movie = Movie(id=id, title=title, year=year)
                        db.session.add(movie)
                        genres = row[2].split('|')  # genres is a list of genres
                        for genre in genres:  # add each genre to the movie_genre table
                            movie_genre = MovieGenre(movie_id=id, genre=genre)
                            db.session.add(movie_genre)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " movies read")

        print("Finished reading in movies \n")

    if MovieLinks.query.count() == 0:
        # read movie links from csv
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
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie link: " + movie_id)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " movie links read")

        print("Finished reading in links \n")

    if MovieTags.query.count() == 0:
        # read movie tags from csv
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
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Integrity error for tag: " + tag)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " movie tags read")

        print("Finished reading in tags \n")
