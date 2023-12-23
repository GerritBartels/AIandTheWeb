import random
import tensorflow as tf

from models import MovieRatings


class Recommender(tf.keras.Model):
    """Movie recommender model that predicts ratings for movies given a user."""

    def __init__(
        self,
        hidden_size: int,
        embedding_dim: int,
        dropout: float,
        num_users: int,
        num_movies: int,
    ) -> None:
        """Initializes the recommender model.

        Arguments:
            hidden_size (int): The number of nodes in each hidden layer.
            embedding_dim (int): The size of the embedding vectors.
            dropout (float): The dropout rate.
            num_users (int): The number of users in the dataset.
            num_movies (int): The number of movies in the dataset.
        """

        super(Recommender, self).__init__()

        self.user_embedding = tf.keras.layers.Embedding(num_users, embedding_dim)
        self.movie_embedding = tf.keras.layers.Embedding(num_movies, embedding_dim)

        self.dense1 = tf.keras.layers.Dense(hidden_size / 2, activation="relu")
        self.dropout1 = tf.keras.layers.Dropout(dropout)
        self.batch_norm1 = tf.keras.layers.BatchNormalization()

        self.dense2 = tf.keras.layers.Dense(hidden_size / 2, activation="relu")
        self.dropout2 = tf.keras.layers.Dropout(dropout)
        self.batch_norm2 = tf.keras.layers.BatchNormalization()

        self.dense3 = tf.keras.layers.Dense(hidden_size, activation="relu")
        self.dropout3 = tf.keras.layers.Dropout(dropout)
        self.batch_norm3 = tf.keras.layers.BatchNormalization()

        self.dense4 = tf.keras.layers.Dense(hidden_size / 2, activation="relu")
        self.dropout4 = tf.keras.layers.Dropout(dropout)
        self.batch_norm4 = tf.keras.layers.BatchNormalization()

        self.dense5 = tf.keras.layers.Dense(hidden_size / 4, activation="relu")
        self.dropout5 = tf.keras.layers.Dropout(dropout)
        self.batch_norm5 = tf.keras.layers.BatchNormalization()

        self.output_layer = tf.keras.layers.Dense(1, activation="sigmoid")

    def call(self, inputs, training=True) -> tf.Tensor:
        """Performs forward pass on the model.

        Arguments:
            inputs (tf.Tensor): The input tensor containing the user and movie ids.

        Returns:
            output (tf.Tensor): The output tensor containing the predicted ratings.
        """

        user_vector = self.user_embedding(inputs[:, 0], training=training)
        user_vector = self.dense1(user_vector, training=training)
        user_vector = self.dropout1(user_vector, training=training)
        user_vector = self.batch_norm1(user_vector, training=training)

        movie_vector = self.movie_embedding(inputs[:, 1], training=training)
        movie_vector = self.dense2(movie_vector, training=training)
        movie_vector = self.dropout2(movie_vector, training=training)
        movie_vector = self.batch_norm2(movie_vector, training=training)

        x = self.dense3(
            tf.concat([user_vector, movie_vector], axis=1), training=training
        )
        x = self.dropout3(x, training=training)
        x = self.batch_norm3(x, training=training)

        x = self.dense4(x, training=training)
        x = self.dropout4(x, training=training)
        x = self.batch_norm4(x, training=training)

        x = self.dense5(x, training=training)
        x = self.dropout5(x, training=training)
        x = self.batch_norm5(x, training=training)

        output = self.output_layer(x, training=training)

        return output


def build_dataset(split: float) -> (tf.data.Dataset, tf.data.Dataset, list, list):
    """Builds the dataset for the recommender model.

    Arguments:
        split (float): The train test split.

    Returns:
        train_data (tf.data.Dataset): The training dataset.
        test_data (tf.data.Dataset): The testing dataset.
    """

    train_data = []

    movie_ratings = MovieRatings.query.all()

    random.shuffle(movie_ratings)

    input_data = []
    target_data = []

    for row in movie_ratings:
        input_data.append([row.user_id, row.movie_id])
        target_data.append(row.rating / 5)

    train_data = tf.data.Dataset.from_tensor_slices(
        (
            input_data[: int(len(input_data) * split)],
            target_data[: int(len(input_data) * split)],
        )
    )
    test_data = tf.data.Dataset.from_tensor_slices(
        (
            input_data[int(len(input_data) * split) :],
            target_data[int(len(input_data) * split) :],
        )
    )

    return train_data, test_data


def train_model(
    hidden_size,
    embedding_dim,
    dropout,
    batch_size,
    learning_rate,
    epochs,
    num_users,
    num_movies,
) -> None:
    """Trains the recommender model.

    Arguments:
        hidden_size (int): The number of nodes in each hidden layer.
        embedding_dim (int): The size of the embedding vectors.
        dropout (float): The dropout rate.
        batch_size (int): The batch size.
        learning_rate (float): The learning rate.
        epochs (int): The number of epochs to train for.
        num_users (int): The number of users in the dataset.
        num_movies (int): The number of movies in the dataset.
    """

    train_data, test_data = build_dataset(0.8)

    model = Recommender(
        hidden_size=hidden_size,
        embedding_dim=embedding_dim,
        dropout=dropout,
        num_users=num_users,
        num_movies=num_movies,
    )

    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)

    model.compile(
        optimizer=optimizer,
        loss=tf.keras.losses.MeanSquaredError(),
        metrics=[tf.keras.metrics.MeanAbsoluteError()],
    )

    model.fit(
        train_data.shuffle(100000).batch(batch_size),
        epochs=epochs,
        validation_data=test_data.batch(batch_size),
    )

    model.save_weights("weights/recommender_weights")
