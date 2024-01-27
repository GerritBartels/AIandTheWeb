# Flask Movie Recommender

This project is a simple movie recommender built with Flask, Flask-User, Flask-Sqlalchemy and Tensorflow.

## Showcase



## Features

- **Web Interface**: The movie recommender provides a simple yet visually appealing web interface built with Flask. Users can register or log in to browse a list of stored films, give them their personal rating, query the database for their favourite movies or get custom recommendations on what to watch next from a neural recommendation model created with Tensorflow. Navigation is facilitated by a hamburger menu (for access to the other functions) or a clickable logo (which takes the user back to the homepage).
- **User Management**:  Flask-User handles the registration, login, and logout processes and protects some routes to be only accessible to logged-in users.
- **Relational databases**: All data is stored in SQLite databases for efficient access, including adding new data and updating data.
- **Homepage**: The homepage is accesible to everyone and welcomes visitors with a carousel overview of top movies, a varying selection of films to discover and links to the other features.
- **Movies**: Logged-in users can browse through a list of all stored films and view additional information such as the average star rating, the film poster, the plot description and links to imdb and tmdb. In addition, users have the option of rating each film using a star system or adjusting their previous rating.
- **Search**: Logged-in users can query the movies database, with the results being fuzzily matched based on the Levenshtein Distance to overcome spelling mistakes. Internally, flask-sqlalchemy is used to make queries in a simple, object-oriented way without using SQL directly.
- **Nerual Recommender**: A neural recommendation model created with Tensorflow provides logged-in users with film suggestions. Both films and users are represented by learnt embeddings, with recommendations being based on the match between the two. The cold start problem is addressed by assigning new users the average embedding calculated across all users.
- **Schedueld Training**: The neural recommendation model is kept up to date by being regularly retrained as soon as a certain number of new user interactions have been recorded.


## Usage

1. Clone the repository. 
2. Change directory: `cd MovieRecommender`
3. Install the required dependencies: `pip install -r requirements.txt`
4. Instantiate the database: `flask --app recommender.py initdb --rebuild`
5. Train the recommender: `flask --app recommender.py train`
3. Run the Flask app: `python flask_search_engine.py`
