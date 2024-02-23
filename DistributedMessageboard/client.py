from pathlib import Path

__location__ = Path(__file__).parent.resolve()

import sys

sys.path.insert(1, __location__.__str__())

import os

os.chdir(__location__)

import requests
import datetime
import sqlalchemy
import urllib.parse
from typing import Union
from sqlalchemy import event, desc
from flask.wrappers import Response
from sqlalchemy.engine import Engine
from models import db, User, Channel, ChannelMessage
from flask import Flask, request, render_template, jsonify, url_for, redirect


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
    """Flask application config"""

    # Flask-SQLAlchemy settings
    # Here a file-based SQL database
    SQLALCHEMY_DATABASE_URI = "sqlite:///channel_database.sqlite"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app = Flask(__name__)
app.config.from_object(__name__ + ".ConfigClass")
app.app_context().push()
db.init_app(app)
db.create_all()

HUB_AUTHKEY = "1234567890"
HUB_URL = "http://localhost:5555"

CHANNELS = None
LAST_CHANNEL_UPDATE = None


def truncate(input: str, length: int=35, suffix: str=' ...') -> str:
    """Truncate a string to a certain length.
    
    Arguments:
        input (str): The input string.
        length (int): The length to truncate to. Defaults to 50.
        suffix (str): The suffix to append to the truncated string. Defaults to '...'.

    Returns:
        (str): The truncated string.
    """

    if len(input) > length:

        return input[:length].rsplit(' ', 1)[0]+suffix
    
    return input


app.jinja_env.filters['truncate'] = truncate


@app.cli.command("initdb")
def initdb_command() -> None:
    """Initialize the database."""

    db.drop_all()
    db.create_all()

    # Create a test user and rasa chatbot
    test_user = User(username="test_user")
    rasa = User(username="Rasa")
    db.session.add(test_user)
    db.session.add(rasa)
    db.session.commit()

    print("Database initialized and test user created.")


def update_channels() -> list:
    """Update the list of channels from the server.

    Returns:
        CHANNELS (list): A list of channels.
    """

    global CHANNELS, LAST_CHANNEL_UPDATE

    if (
        CHANNELS
        and LAST_CHANNEL_UPDATE
        and (datetime.datetime.now() - LAST_CHANNEL_UPDATE).seconds < 60
    ):
        return CHANNELS

    # Fetch list of channels from server
    response = requests.get(
        HUB_URL + "/channels", headers={"Authorization": "authkey " + HUB_AUTHKEY}
    )

    if response.status_code != 200:
        return "Error fetching channels: " + str(response.text), 400

    channels_response = response.json()

    if not "channels" in channels_response:
        return "No channels in response", 400

    CHANNELS = channels_response["channels"]
    LAST_CHANNEL_UPDATE = datetime.datetime.now()

    return CHANNELS


def update_and_get_messages(channel_name: str) -> tuple:
    """Update the list of messages from a channel.

    Arguments:
        channel_name (str): The name of the channel.

    Returns:
        (tuple): A tuple containing the channel and the messages.
    """

    if not channel_name:
        return "No channel specified", 400

    channel = None

    for c in update_channels():
        if c["endpoint"] == urllib.parse.unquote(channel_name):
            channel = c
            break

    if not channel:
        return "Channel not found", 404

    
    response = requests.get(
        channel["endpoint"],
        headers={"Authorization": "authkey " + channel["authkey"]},
    )

    if response.status_code != 200:
        return "Error fetching messages: " + str(response.text), 400

    messages = response.json()

    return channel, messages


@app.route("/")
def home_page() -> str:
    """Return list of channels.

    Returns:
        (str): The home page.
    """

    # Fetch all users and local channels from database
    users = User.query.filter(User.username != 'Rasa').all()
    local_channels = Channel.query.all()

    # Fetch the last message for each local channel
    for channel in local_channels:
        last_message = (
            ChannelMessage.query.filter_by(channel_id=channel.id)
            .order_by(desc(ChannelMessage.timestamp))
            .first()
        )
        channel.last_message = (
            last_message.content if last_message else "No messages here."
        )
        channel.last_message_sender = last_message.sender if last_message else ""

    remote_channels = update_channels()

    # Remove local channels from remote channels
    for local_channel in local_channels:
        for remote_channel in remote_channels:
            if local_channel.endpoint == remote_channel["endpoint"]:
                remote_channels.remove(remote_channel)

    return render_template(
        "home.html",
        remote_channels=remote_channels,
        users=users,
        local_channels=local_channels,
    )


@app.route("/retrieve_last_message/<string:channel_name>", methods=["GET"])
def retrieve_last_message(channel_name: str) -> Response:
    """Return the last message for a channel.

    Arguments:
        channel_name (str): The name of the channel.

    Returns:
        (Response): The last message for the channel.
    """

    channel_id = Channel.query.filter_by(name=channel_name).first().id

    last_message = (
        ChannelMessage.query.filter_by(channel_id=channel_id)
        .order_by(desc(ChannelMessage.timestamp))
        .first()
    )

    return jsonify(
        {
            "channel_id": channel_id,
            "last_message": last_message.content if last_message else "No messages here.",
            "last_message_sender": last_message.sender if last_message else "",
        }
    )


@app.route("/show")
def show_channel() -> Union[tuple[str, int], str]:
    """Return list of messages for a channel.

    Returns:
        (Union[tuple[str, int], str]): A tuple containing the response message and the status code,
            or the rendered channel page.
    """
    channel_name = request.args.get("channel", None)
    sender = request.args.get("sender", None)

    channel, messages = update_and_get_messages(channel_name)

    if isinstance(messages, int):
        return channel, messages

    for message in messages:
        date = datetime.datetime.strptime(
            message["timestamp"], "%Y-%m-%dT%H:%M:%S.%f"
        ).date()
        time = datetime.datetime.strptime(message["timestamp"], "%Y-%m-%dT%H:%M:%S.%f")

        time = time.strftime("%H:%M")

        message["date"] = date
        message["time"] = time

    return render_template(
        "channel.html",
        channel=channel,
        messages=messages,
        sender=sender,
    )


@app.route("/post", methods=["POST"])
def post_message() -> Union[tuple[str, int], str]:
    """Post a message to a channel.

    Returns:
        (Union[tuple[str, int], str]): A tuple containing the response message and the status code,
            or the rendered channel page.
    """

    post_channel = request.form["channel"]

    if not post_channel:
        return "No channel specified", 400

    channel = None

    for c in update_channels():
        if c["endpoint"] == urllib.parse.unquote(post_channel):
            channel = c
            break

    if not channel:
        return "Channel not found", 404

    message_content = request.form["content"]
    message_sender = request.form["sender"]
    message_timestamp = datetime.datetime.now().isoformat()

    response = requests.post(
        channel["endpoint"],
        headers={"Authorization": "authkey " + channel["authkey"]},
        json={
            "content": message_content,
            "sender": message_sender,
            "timestamp": message_timestamp,
        },
    )

    if response.status_code != 200:
        return "Error posting message: " + str(response.text), 400

    channel, messages = update_and_get_messages(channel["endpoint"])

    if isinstance(messages, int):
        return channel, messages

    for message in messages:
        date = datetime.datetime.strptime(
            message["timestamp"], "%Y-%m-%dT%H:%M:%S.%f"
        ).date()
        time = datetime.datetime.strptime(message["timestamp"], "%Y-%m-%dT%H:%M:%S.%f")

        time = time.strftime("%H:%M")

        message["date"] = date
        message["time"] = time

    return render_template(
        "channel.html",
        channel=channel,
        messages=messages,
        sender=message_sender,
    )


@app.route("/add_user", methods=["POST"])
def add_user() -> Union[tuple[Response, int], Response]:
    """Add a user to the database.

    Returns:
        (Union[tuple[Response, int], Response]): A tuple containing the response message and the status code,
            or just the response message.
    """

    data = request.get_json()
    username = data.get("username")

    if username:
        user = User(username=username)
        try:
            db.session.add(user)
            db.session.commit()
            return jsonify({"success": True})
        except sqlalchemy.exc.IntegrityError:
            print("error caputerd")
            db.session.rollback()
            return (
                jsonify(
                    {"success": False, "message": "Username is already registered"}
                ),
                409,
            )
    else:
        return jsonify({"success": False, "message": "Username is required"}), 400


# Start development web server
if __name__ == "__main__":
    app.run(port=5005, debug=True)
