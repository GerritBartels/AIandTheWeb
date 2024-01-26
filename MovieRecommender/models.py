from flask_user import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()


class User(db.Model, UserMixin):
    """User account model. Stores user information and authentication details.
    Has a one-to-many relationship with MovieTags and MovieRatings.
    """

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    active = db.Column("is_active", db.Boolean(), nullable=False, server_default="1")

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    username = db.Column(
        db.String(100, collation="NOCASE"), nullable=False, unique=True
    )
    password = db.Column(db.String(255), nullable=False, server_default="")
    email_confirmed_at = db.Column(db.DateTime())

    # User information
    first_name = db.Column(
        db.String(100, collation="NOCASE"), nullable=False, server_default=""
    )
    last_name = db.Column(
        db.String(100, collation="NOCASE"), nullable=False, server_default=""
    )
    tags = db.relationship("MovieTags", backref="user", lazy=True)
    ratings = db.relationship("MovieRatings", backref="user", lazy=True)


class Movie(db.Model):
    """Movie model. Stores movie title and publication year.
    Has a one-to-many relationship with MovieGenre, MovieLinks, MovieTags, and MovieRatings.
    """

    __tablename__ = "movies"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100, collation="NOCASE"), nullable=False, unique=True)
    year = db.Column(db.Integer, nullable=False)
    genres = db.relationship("MovieGenre", backref="movie", lazy=True)
    links = db.relationship("MovieLinks", backref="movie", lazy=True)
    tags = db.relationship("MovieTags", backref="movie", lazy=True)
    ratings = db.relationship("MovieRatings", backref="movie", lazy=True)
    avg_rating = db.Column(db.Float, nullable=False, server_default="0.0")
    num_ratings = db.Column(db.Integer, nullable=False, server_default="0")


class MovieGenre(db.Model):
    """Movie genre model. Stores movie id and genres."""

    __tablename__ = "movie_genres"
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False)
    genre = db.Column(db.String(255), nullable=False, server_default="")


class MovieLinks(db.Model):
    """Movie links model. Stores movie id, imdb id, and tmdb id used for linking to these external."""

    __tablename__ = "movie_links"
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(
        db.Integer, db.ForeignKey("movies.id"), nullable=False, unique=True
    )
    imdb_id = db.Column(db.String(255), nullable=False, server_default="")
    tmdb_id = db.Column(db.String(255), nullable=False, server_default="")


class MovieTags(db.Model):
    """Movie tags model. Stores user id, movie id, and tags.
    A UniqueConstraint is used to prevent duplicate tags for a given user and movie.
    """

    __tablename__ = "movie_tags"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False)
    tag = db.Column(db.String(255), nullable=False, server_default="")
    timestamp = db.Column(db.DateTime())

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", "tag", name="user_movie_tag_uc"),
    )


class MovieRatings(db.Model):
    """Movie ratings model. Stores user id, movie id, and ratings.
    A UniqueConstraint is used to prevent duplicate ratings for a given user and movie.
    """

    __tablename__ = "movie_ratings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime())

    __table_args__ = (UniqueConstraint("user_id", "movie_id", name="user_movie_uc"),)
