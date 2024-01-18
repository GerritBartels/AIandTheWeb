# Contains parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html
from pathlib import Path

__location__ = Path(__file__).parent.resolve()

import sys

sys.path.insert(1, __location__.__str__())

import os

os.chdir(__location__)

import click
import sqlite3
import datetime
import numpy as np
import tensorflow as tf
from threading import Lock
from fuzzywuzzy import fuzz
from werkzeug.wrappers import Response

from flask import Flask, render_template, flash, request, redirect, session, url_for

from flask_user.signals import user_registered
from flask_user import login_required, UserManager, current_user

from apscheduler.schedulers.background import BackgroundScheduler

from sqlalchemy.engine import Engine
from sqlalchemy import event, not_, case
from sqlalchemy.exc import IntegrityError

from models import db, User, Movie, MovieRatings
from recommender_model import Recommender, train_model
from utils import check_and_read_data, get_movie_metadata, CustomPagination

# Register numpy int32 as a converter to sqlite3
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
    SECRET_KEY = "TheSecretestKeyToHaveRoamedThisPlanet"

    # Flask-SQLAlchemy settings
    # Here a file-based SQL database
    SQLALCHEMY_DATABASE_URI = "sqlite:///movie_recommender.sqlite"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-User settings
    USER_APP_NAME = "Movie Recommender"
    USER_ENABLE_EMAIL = False
    USER_ENABLE_USERNAME = True
    USER_REQUIRE_RETYPE_PASSWORD = True

    # Make sure that the user is redirected to the home page after login, logout, etc.
    USER_AFTER_REGISTER_ENDPOINT = 'home_page'
    USER_AFTER_CONFIRM_ENDPOINT = 'home_page'
    USER_AFTER_LOGIN_ENDPOINT = 'home_page'
    USER_AFTER_LOGOUT_ENDPOINT = 'home_page'


# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + ".ConfigClass")
app.app_context().push()
db.init_app(app)
db.create_all()
user_manager = UserManager(app, db, User)

# Used to retrain the recommender model every n new ratings
RETRAIN_EVERY = 100
new_ratings_counter = 1

# Define lock. Used to prevent user registration while
# training the recommender model
retraining_lock = Lock()

if "initdb" not in sys.argv:
    HIDDEN_SIZE = 2048
    EMBEDDING_DIM = 512
    DROPOUT = 0.2
    BATCH_SIZE = 512
    LEARNING_RATE = 0.001
    EPOCHS = 10
    NUM_UNIQUE_USERS = len(User.query.with_entities(User.id).all())
    UNIQUE_MOVIES = Movie.query.with_entities(Movie.id).all()
    UNIQUE_MOVIES_VOCAB = [str(movie[0]) for movie in UNIQUE_MOVIES]
    NUM_UNIQUE_MOVIES = len(UNIQUE_MOVIES)

    if "train" not in sys.argv:
        print("Loading recommender model...")
        # Load recommender model with the latest weights
        recommender_model = Recommender(
            hidden_size=HIDDEN_SIZE,
            embedding_dim=EMBEDDING_DIM,
            dropout=DROPOUT,
            num_users=NUM_UNIQUE_USERS,
            num_movies=NUM_UNIQUE_MOVIES,
            movie_vocab=UNIQUE_MOVIES_VOCAB,
        )
        recommender_model.load_weights("weights/recommender_weights")
        recommender_model.build((None, 2))
        print("Recommender model weights loaded.")


@app.cli.command("initdb")
@click.option("--rebuild", is_flag=True, help="Rebuild the entire database.")
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
    print("Initialized the database.")


@app.cli.command("train")
def train_command() -> None:
    """Trains the recommender model."""

    print("Training recommender model...")
    train_model(
        hidden_size=HIDDEN_SIZE,
        embedding_dim=EMBEDDING_DIM,
        dropout=DROPOUT,
        batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        epochs=EPOCHS,
        num_users=NUM_UNIQUE_USERS,
        num_movies=NUM_UNIQUE_MOVIES,
        movie_vocab=UNIQUE_MOVIES_VOCAB,
    )
    print("Trained the model.")


@app.template_filter("isinteger")
def isinteger(value: any) -> bool:
    """Checks if a value is an integer. Used in the movies template.

    Arguments:
        value (any): The value to check.

    Returns:
        is_int (bool): Whether the value is an integer.
    """

    is_int = isinstance(value, int)

    return is_int


@user_registered.connect_via(app)
def _after_register_hook(sender, user, **extra) -> None:
    """Adds the user to the recommender model after registration.
    In case the recommender model is being trained, the user is added after training.

    Arguments:
        sender (flask.Flask): The Flask app.
        user (User): The user that was registered.
        extra (dict): Extra arguments.
    """
    with retraining_lock:
        recommender_model.add_user()


def retrain_recommender_model() -> None:
    """Retrains the recommender model every 100 new ratings."""

    global new_ratings_counter

    with retraining_lock:
        with app.app_context():
            if new_ratings_counter % RETRAIN_EVERY == 0:
                UNIQUE_USERS = len(User.query.with_entities(User.id).all())

                print("Retraining recommender model...")
                train_model(
                    hidden_size=HIDDEN_SIZE,
                    embedding_dim=EMBEDDING_DIM,
                    dropout=DROPOUT,
                    batch_size=BATCH_SIZE,
                    learning_rate=LEARNING_RATE,
                    epochs=EPOCHS,
                    num_users=UNIQUE_USERS,
                    num_movies=NUM_UNIQUE_MOVIES,
                    movie_vocab=UNIQUE_MOVIES_VOCAB,
                )
                print("Retrained the model.")

                recommender_model.load_weights("weights/recommender_weights")
                recommender_model.build((None, 2))

                print("Retrained recommender model weights loaded.")
                new_ratings_counter = 1


# Create and start background scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=retrain_recommender_model, trigger="interval", minutes=0.5)
scheduler.start()


@app.route("/")
def home_page() -> str:
    """Renders the home page.

    Returns:
        str: Rendered home page.
    """

    return render_template("home.html")


@app.route("/save_scroll", methods=["POST"])
def save_scroll() -> (str, int):
    """Saves the scroll position of the movies page.
    Needed because rating a movie redirects to the movies page and the scroll position is lost otherwise.

    Returns:
        str: Empty string.
        204: No content.
    """
    session["scroll_position"] = request.form.get("scroll_position")
    return "", 204
    

@app.route("/movies", methods=["GET"])
@login_required
def movies() -> str:
    """Renders the movies page. Displays the 10 movies on the current page
    as well as their tags, average ratings, and the logged in user's rating.

    Returns:
        str: Rendered movies page.
    """

    page = request.args.get("page", 1, type=int)
    movies = Movie.query.paginate(page=page, per_page=10)

    # Get movie tags, average ratings, and user ratings
    movie_tags, average_ratings, user_ratings = get_movie_metadata(
        db=db, movies=movies, current_user=current_user
    )

    return render_template(
        "movies.html",
        movies=movies,
        movie_tags=movie_tags,
        average_ratings=average_ratings,
        user_ratings=user_ratings,
    )


@app.route("/movies_search", methods=["GET"])
@login_required
def movies_search() -> str:
    """Renders the movies search page. Displays 10 searched movies per page."""
    
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("query", "", type=str)

    if search_query:
        all_movies = Movie.query.all()

        # Calculate fuzzy ratios and store them with the corresponding movie in a list of tuples
        movie_ratios = [(movie, fuzz.ratio(movie.title.lower(), search_query.lower())) for movie in all_movies]

        # Sort the list of tuples based on the fuzzy ratio
        movie_ratios.sort(key=lambda x: x[1], reverse=True)

        # Find the index where the fuzzy ratio falls below the threshold
        threshold = 45  # Set your desired threshold here
        index = next((index for index, (movie, ratio) in enumerate(movie_ratios) if ratio < threshold), len(movie_ratios))

        # Discard movies that don't meet the threshold and store their IDs in the session
        session["all_searched_movie_ids"] = [movie.id for movie, ratio in movie_ratios[:index]]

    # If no search query was provided, redirect to the movies page
    # If no movies were found, display a flash message
    if session.get("all_searched_movie_ids") is None:
        flash("No search query was provided", "error")
        return redirect(url_for("movies"))

    elif len(session["all_searched_movie_ids"]) == 0:
        flash("No movies were found", "error")
        return render_template("movies_search.html", movies={}, movie_tags={}, average_ratings={}, user_ratings={})

    total = len(session["all_searched_movie_ids"])
    movie_ids = session["all_searched_movie_ids"][(page-1)*10 : page*10]

    # Query the database to get the movie objects
    movies = Movie.query.filter(Movie.id.in_(movie_ids)).all()

    # Create a dictionary with movie IDs as keys and movies as values
    movies_dict = {movie.id: movie for movie in movies}

    # Sort the movies based on the order of IDs in movie_ids
    movies = [movies_dict[id] for id in movie_ids]

    movies = CustomPagination(movies, page, 10, total)

    movie_tags, average_ratings, user_ratings = get_movie_metadata(
        db=db, movies=movies, current_user=current_user
    )

    return render_template(
        "movies_search.html",
        movies=movies, 
        movie_tags=movie_tags,
        average_ratings=average_ratings,
        user_ratings=user_ratings,
    )


@app.route("/rate_movie", methods=["POST"])
@login_required
def rate_movie() -> Response:
    """Endpoint for rating a movie. Redirects to the movies page after rating has been saved.
    Displays a flash message if rating was successful or if an error occurred.

    Returns:
        Response: Redirects to the movies page.
    """

    global new_ratings_counter

    movie_id = int(request.form["movie_id"])
    rating = float(request.form["rating"])

    # Adapt flash cards depending on where the user came from
    if request.referrer.endswith(url_for("movie_recommender")):
        flash_category = "success"
    else:
        flash_category = movie_id

    try:
        # Check if rating already exists for the given movie and current logged in user
        if (
            MovieRatings.query.filter_by(
                user_id=current_user.id, movie_id=movie_id
            ).count()
            == 0
        ):
            movie_rating = MovieRatings(
                user_id=current_user.id,
                movie_id=movie_id,
                rating=rating,
                timestamp=datetime.date.today(),
            )
            db.session.add(movie_rating)
            db.session.commit()
            flash("Movie rated successfully", flash_category)

        else:
            movie_rating = MovieRatings.query.filter_by(
                user_id=current_user.id, movie_id=movie_id
            ).first()

            if not movie_rating.rating == rating:
                movie_rating.rating = rating
                movie_rating.timestamp = datetime.date.today()
                db.session.commit()
                flash("Rating updated successfully", flash_category)

        new_ratings_counter += 1

    except IntegrityError:
        db.session.rollback()
        flash("An error occurred while rating the movie", "error")

    return redirect(request.referrer)


@app.route("/movie_recommender")
@login_required
def movie_recommender() -> str:
    """Renders the movie recommender page. Calls recommender model on
    all unseen movies of the logged in user and gets their movie objects + metadata.

    Returns:
        str: Rendered movie recommender page.
    """

    user_id = current_user.id

    # Get all movie IDs that the current user has rated
    rated_movies = MovieRatings.query.filter_by(user_id=user_id).with_entities(
        MovieRatings.movie_id
    )
    # Get all movies not in rated_movies
    unrated_movies = (
        Movie.query.filter(not_(Movie.id.in_(rated_movies)))
        .with_entities(Movie.id)
        .all()
    )

    user_id = np.expand_dims(np.asarray([user_id] * len(unrated_movies)), axis=1)
    unrated_movies = np.asarray(unrated_movies)

    # Get recommendations for the current user
    # Subtract 1 from user_id and movie_id to make them zero-indexed
    data = tf.convert_to_tensor(
        np.concatenate((user_id - 1, unrated_movies - 1), axis=1)
    )
    predictions = recommender_model(data, training=False).numpy()
    recommender_model.add_user()

    # Combine movie IDs and predictions into a dictionary and sort by prediction
    recommendations_dict = dict(zip(unrated_movies.flatten(), predictions.flatten()))
    recommendations_dict = dict(
        sorted(recommendations_dict.items(), key=lambda x: x[1], reverse=True)
    )

    # Get the top 50 recommendations, their movie objects and metadata
    recommendation_ids = list(recommendations_dict.keys())[:50]

    # Define the ordering
    order = case(
        {id: index for index, id in enumerate(recommendation_ids)}, value=Movie.id
    )
    movie_recommendations = (
        Movie.query.filter(Movie.id.in_(recommendation_ids)).order_by(order).all()
    )
    movie_tags, average_ratings, _ = get_movie_metadata(
        db=db,
        movies=movie_recommendations,
        current_user=current_user,
        get_user_ratings=False,
    )

    rating_weights = {
        key: value[0] * value[1] for key, value in average_ratings.items()
    }

    # Find the minimum and maximum values
    min_val = min(rating_weights.values())
    max_val = max(rating_weights.values())

    # Apply min-max normalization and add a small random value to each rating for diversity
    rating_weights = {
        key: (((value - min_val) / (max_val - min_val)) * 0.05)
        + utility
        + np.random.uniform(0, 0.05)
        for (key, value), utility in zip(
            rating_weights.items(), list(recommendations_dict.values())[:200]
        )
    }
    rating_weights = dict(
        sorted(rating_weights.items(), key=lambda x: x[1], reverse=True)
    )

    order = case({id: index for index, id in enumerate(rating_weights)}, value=Movie.id)
    movie_recommendations = (
        Movie.query.filter(Movie.id.in_(list(rating_weights))).order_by(order).all()
    )

    return render_template(
        "movie_recommender.html",
        movie_recommendations=movie_recommendations,
        movie_tags=movie_tags,
        average_ratings=average_ratings,
    )

# Start development web server
if __name__ == "__main__":
    app.run(port=5000, debug=True)
