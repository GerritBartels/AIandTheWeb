# Flask Movie Recommender

This project is a movie recommender system developed using Flask, Flask-User, Flask-Sqlalchemy, TensorFlow and the MovieLens 100k dataset. It seemlessly combines intuitive user interaction, robust database management and neural network based recommendations.

## Showcase

![Movie_Recommender_Demo](https://github.com/GerritBartels/AIandTheWeb/assets/64156238/b2693f09-06d6-49db-9bc8-fe99253d8e6e)


## Features

- **Web Interface**: The movie recommender provides a sleek, visually appealing web interface built with Flask. Users can register or log in to browse a list of stored films, give them their personal rating, query the database for their favourite movies or get custom recommendations on what to watch next from a neural recommendation model created with TensorFlow. Navigation is facilitated by a burger menu and a navigation bar.
- **User Management**:  Flask-User handles the registration, login, and logout processes. Certain routes are protected and accessible only to logged-in users, ensuring a secure and personalized experience.
- **Relational databases**: All data is stored in SQLite databases for efficient access, including adding new data and updating data.
- **Homepage**: The homepage welcomes all visitors with a carousel overview of top movies, a varying selection of films to discover and links to the other features.
- **Movies**: Logged-in users can browse through a list of all stored films and view additional information such as the average star rating, the film poster, the plot description and links to IMDb and TMDB. In addition, users have the option of rating each film using a star system or adjusting their previous rating.
- **Search**: Logged-in users can query the movie database, with the results being fuzzily matched based on the Levenshtein Distance to overcome spelling mistakes. Internally, flask-sqlalchemy is used to make queries in a simple, object-oriented way without using SQL directly.
- **Neural Recommender**: A neural recommendation model created with TensorFlow provides logged-in users with movie suggestions. Both movies and users are represented by learnt embeddings that guide the neural network for providing personalized recommendations. The cold start problem is addressed by assigning new users the average embedding calculated across all users.
- **Scheduled Training**: The neural recommendation model is kept up-to-date by being regularly retrained as soon as a certain number of new user interactions have been recorded. This ensures the system continuously adapts to evolving user preferences.


## Usage

1. Clone the repository. 
2. Change directory: `cd MovieRecommender`
3. Install the required dependencies: `pip install -r requirements.txt`
4. Instantiate the database: `flask --app recommender.py initdb`
   4.1 To entirely rebuild an existing database add the `--rebuild` flag
5. Train the recommender: `flask --app recommender.py train`
6. Run the Flask app: `python recommender.py`

Optionally the larger variants of the [MovieLens](https://grouplens.org/datasets/movielens/) dataset may be used if desired. 
