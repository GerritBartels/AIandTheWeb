# Contains parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html
from pathlib import Path

__location__ = Path(__file__).parent.resolve()

import sys

sys.path.insert(1, __location__.__str__())

import os

os.chdir(__location__)

from flask import Flask, render_template
from flask_user import login_required, UserManager, current_user

from models import db, User, Movie, MovieGenre, MovieRatings
from read_data import check_and_read_data

from sqlalchemy.engine import Engine
from sqlalchemy import event

from collections import Counter

from flask import request, redirect, url_for

import datetime


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'TheSecretestKeyToHaveRoamedThisPlanet'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///movie_recommender.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    # Flask-User settings
    USER_APP_NAME = "Movie Recommender"  # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = False  # Disable email authentication
    USER_ENABLE_USERNAME = True  # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = True  # Simplify register form

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary
user_manager = UserManager(app, db, User)  # initialize Flask-User managemen


@app.cli.command('initdb')
def initdb_command():
    global db
    """Creates the database tables."""
    check_and_read_data(db=db, user_manager=user_manager)
    print('Initialized the database.')

# The Home page is accessible to anyone
@app.route('/')
def home_page():
    # render home.html template
    return render_template("home.html")


# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/movies')
@login_required  # User must be authenticated
def movies():

    # first 20 movies
    movies = Movie.query.limit(20).all()

    # get movie tags for each movie, sort them by tag count first and then alphabetically
    movie_tags = {}
    for movie in movies:
        if movie.tags:
            tag_counts = Counter([tag.tag.lower() for tag in movie.tags])
            sorted_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))
            sorted_tags = [key.title() for key in dict(sorted_tags).keys()]
            movie_tags[movie.id] = sorted_tags

    return render_template("movies.html", movies=movies, movie_tags=movie_tags)


@app.route('/rate_movie', methods=['POST'])
@login_required
def rate_movie():

    movie_id = int(request.form['movie_id'])
    rating = int(request.form['rating'])

    # check if rating already exists
    if MovieRatings.query.filter_by(user_id=current_user.id, movie_id=movie_id).count() == 0:
        movie_rating = MovieRatings(user_id=current_user.id, movie_id=movie_id, rating=rating, timestamp=datetime.date.today())
        db.session.add(movie_rating)
        db.session.commit()
    else:
        movie_rating = MovieRatings.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
        movie_rating.rating = rating
        movie_rating.timestamp = datetime.date.today()
        db.session.commit()

    return redirect(url_for('movies'))
    


# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)
