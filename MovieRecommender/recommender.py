# Contains parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html
from pathlib import Path

__location__ = Path(__file__).parent.resolve()

import sys

sys.path.insert(1, __location__.__str__())

import os

os.chdir(__location__)

import click
import datetime
import numpy as np
import tensorflow as tf
from collections import Counter
from werkzeug.wrappers import Response

from flask import Flask, render_template, flash, request, redirect, session
from flask_user import login_required, UserManager, current_user

from sqlalchemy.engine import Engine
from sqlalchemy import event, not_
from sqlalchemy.exc import IntegrityError

from models import db, User, Movie, MovieRatings
from recommender_model import Recommender, train_model
from utils import check_and_read_data, get_movie_metadata

import sqlite3
sqlite3.register_adapter(np.int32, lambda val: int(val))


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    """Sets the foreign key pragma on SQLite databases.
    
    Arguments:
        dbapi_connection (sqlite3.Connection): Active SQLite connection.
        connection_record (sqlalchemy.pool.base._ConnectionRecord): The connection record.
    """

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class ConfigClass(object):
    """Flask application config."""

    # Key for hashing passwords
    SECRET_KEY = 'TheSecretestKeyToHaveRoamedThisPlanet'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///movie_recommender.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    # Flask-User settings
    USER_APP_NAME = "Movie Recommender"  # Shown in email templates and page footers
    USER_ENABLE_EMAIL = False  # Disable email authentication
    USER_ENABLE_USERNAME = True  # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = True  # Simplify register form


# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary
user_manager = UserManager(app, db, User)  # initialize Flask-User management

if "initdb" not in sys.argv:
    # Get total number of users and movies
    HIDDEN_SIZE = 2048
    EMBEDDING_DIM = 512
    DROPOUT = 0.2
    BATCH_SIZE = 512
    LEARNING_RATE = 0.001
    EPOCHS = 10
    UNIQUE_USERS = len(User.query.with_entities(User.id).all())
    UNIQUE_MOVIES = len(Movie.query.with_entities(Movie.id).all())

    if "train" not in sys.argv:
        print("Loading recommender model...")
        # Load recommender model with the latest weights
        recommender_model = Recommender(hidden_size=HIDDEN_SIZE, 
                                        embedding_dim=EMBEDDING_DIM,
                                        dropout=DROPOUT, 
                                        num_users=UNIQUE_USERS, 
                                        num_movies=UNIQUE_MOVIES)
        recommender_model.load_weights('weights/recommender_weights')
        recommender_model.build((None, 2))
        print("Recommender model weights loaded.")


@app.cli.command('initdb')
@click.option('--rebuild', is_flag=True, help='Rebuild the entire database.')
def initdb_command(rebuild: bool) -> None:
    """Creates the database tables.
    
    Arguments:
        rebuild (bool): Whether to rebuild the entire database.
    """

    if rebuild:
        # Drop existing tables
        db.drop_all()

    # Create new tables
    db.create_all()  

    check_and_read_data(db=db, user_manager=user_manager)
    print('Initialized the database.')


@app.cli.command('train')
def train_command() -> None:
    """Trains the recommender model."""

    print("Training recommender model...")
    train_model(hidden_size=HIDDEN_SIZE, 
                embedding_dim=EMBEDDING_DIM, 
                dropout=DROPOUT, 
                batch_size=BATCH_SIZE, 
                learning_rate=LEARNING_RATE, 
                epochs=EPOCHS, 
                num_users=UNIQUE_USERS, 
                num_movies=UNIQUE_MOVIES)
    print('Trained the model.')


@app.template_filter('isinteger')
def isinteger(value: any) -> bool:
    """Checks if a value is an integer. Used in the movies template.
    
    Arguments:
        value (any): The value to check.
        
    Returns:
        is_int (bool): Whether the value is an integer.
    """

    is_int = isinstance(value, int)

    return is_int


@app.route('/')
def home_page() -> str:
    """Renders the home page.
    
    Returns:
        str: Rendered home page.
    """

    return render_template("home.html")


@app.route('/save_scroll', methods=['POST'])
def save_scroll() -> (str, int):
    """Saves the scroll position of the movies page.
    Needed because rating a movie redirects to the movies page and the scroll position is lost otherwise.
    
    Returns:
        str: Empty string.
        204: No content.
    """
    session['scroll_position'] = request.form.get('scroll_position')
    return '', 204


@app.route('/movies')
@login_required 
def movies() -> str:
    """Renders the movies page. Displays the first 20 movies 
    and their tags, average ratings, and the logged in user's rating.

    Returns:
        str: Rendered movies page.
    """

    # Display first 20 movies
    movies = Movie.query.limit(20).all()

    # Get movie tags, average ratings, and user ratings
    movie_tags, average_ratings, user_ratings = get_movie_metadata(db=db, movies=movies, current_user=current_user)

    return render_template("movies.html", movies=movies, movie_tags=movie_tags, average_ratings=average_ratings, user_ratings=user_ratings)


@app.route('/rate_movie', methods=['POST'])
@login_required
def rate_movie() -> Response:
    """Endpoint for rating a movie. Redirects to the movies page after rating has been saved.
    Displays a flash message if rating was successful or if an error occurred.
    
    Returns:
        Response: Redirects to the movies page.
    """

    try:
        movie_id = int(request.form['movie_id'])
        rating = float(request.form['rating'])

        # Check if rating already exists for the given movie and current logged in user
        if MovieRatings.query.filter_by(user_id=current_user.id, movie_id=movie_id).count() == 0:
            movie_rating = MovieRatings(user_id=current_user.id, movie_id=movie_id, rating=rating, timestamp=datetime.date.today())
            db.session.add(movie_rating)
            db.session.commit()
            flash('Movie rated successfully', movie_id)

        else:
            movie_rating = MovieRatings.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()

            if not movie_rating.rating == rating:
                movie_rating.rating = rating
                movie_rating.timestamp = datetime.date.today()
                db.session.commit()
                flash('Rating updated successfully', movie_id)

    except IntegrityError:
        db.session.rollback()
        flash('An error occurred while rating the movie', 'error')

    return redirect(request.referrer)
    

@app.route('/movie_recommender')
@login_required
def movie_recommender() -> str:
    """Renders the movie recommender page. Calls recommender model on 
    all unseen movies of the logged in user and gets their movie objects + metadata.
    
    Returns:
        str: Rendered movie recommender page.
    """

    user_id = current_user.id

    # Get all movie IDs that the current user has rated
    rated_movies = MovieRatings.query.filter_by(user_id=user_id).with_entities(MovieRatings.movie_id)
    # Get all movies not in rated_movies
    unrated_movies = Movie.query.filter(not_(Movie.id.in_(rated_movies))).with_entities(Movie.id).all()

    user_id = np.expand_dims(np.asarray([user_id]*len(unrated_movies)), axis=1)
    unrated_movies = np.asarray(unrated_movies)

    # Get recommendations for the current user
    data = tf.convert_to_tensor(np.concatenate((user_id, unrated_movies), axis=1))
    predictions = recommender_model(data, training=False).numpy()

    # Combine movie IDs and predictions into a dictionary and sort by prediction
    recommendations_dict = dict(zip(unrated_movies.flatten(), predictions.flatten()))
    recommendations_dict = dict(sorted(recommendations_dict.items(), key=lambda x: x[1], reverse=True))

    # Get the top 20 recommendations, their movie objects and metadata
    recommendation_ids = list(recommendations_dict.keys())[:20]
    movie_recommendations = Movie.query.filter(Movie.id.in_(recommendation_ids)).all()
    movie_tags, average_ratings, _ = get_movie_metadata(db=db, movies=movie_recommendations, current_user=current_user, get_user_ratings=False)

    return render_template("movie_recommender.html", movie_recommendations=movie_recommendations, movie_tags=movie_tags, average_ratings=average_ratings)


# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)

