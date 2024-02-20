from pathlib import Path

__location__ = Path(__file__).parent.resolve()

import sys

sys.path.insert(1, __location__.__str__())

import os

os.chdir(__location__)

import json
import datetime
import requests
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, render_template, jsonify

db = SQLAlchemy()


class Channel(db.Model):
    """Represents a channel in the message board."""

    __tablename__ = "channels"
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column("is_active", db.Boolean(), nullable=False, server_default="1")
    name = db.Column(db.String(100, collation="NOCASE"), nullable=False)
    endpoint = db.Column(
        db.String(100, collation="NOCASE"), nullable=False, unique=True
    )
    authkey = db.Column(db.String(100, collation="NOCASE"), nullable=False)
    last_heartbeat = db.Column(db.DateTime(), nullable=True, server_default=None)


class ConfigClass(object):
    """Flask application config"""

    # Flask settings
    SECRET_KEY = "This is an INSECURE secret!! DO NOT use this in production!!"

    # Flask-SQLAlchemy settings
    # Here a file-based SQL database with warnings turned off
    SQLALCHEMY_DATABASE_URI = "sqlite:///chat_server.sqlite"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + ".ConfigClass")
app.app_context().push()
db.init_app(app)
db.create_all()

SERVER_AUTHKEY = "1234567890"


@app.route("/")
def home_page() -> str:
    """Renders the home page.

    Returns:
        (str): The rendered home page.
    """

    channels = Channel.query.all()

    return render_template("home.html")


def health_check(endpoint: str, authkey: str) -> bool:
    """Check if a channel is healthy.

    Arguments:
        endpoint (str): The endpoint of the channel.
        authkey (str): The authkey of the channel.

    Returns:
        (bool): True if the channel is healthy, False otherwise.
    """

    response = requests.get(
        endpoint + "/health", headers={"Authorization": "authkey " + authkey}
    )

    if response.status_code != 200:
        return False

    # TODO: Check payload
    return True


@app.route("/channels", methods=["POST"])
def create_channel() -> tuple[str, int]:
    """Creates a new channel.

    Returns:
        (tuple[str, int]): A tuple containing the response message and the status code.
    """

    global SERVER_AUTHKEY
    required_headers = ["name", "endpoint", "authkey"]

    record = json.loads(request.data)

    # Check if authorization header is present
    if "Authorization" not in request.headers:
        return "No authorization header", 400

    # Check if authorization header is valid
    if request.headers["Authorization"] != "authkey " + SERVER_AUTHKEY:
        return (
            "Invalid authorization header ({})".format(
                request.headers["Authorization"]
            ),
            400,
        )

    for header in required_headers:
        if header not in record:
            return f"Record has no {header}", 400

    if not health_check(record["endpoint"], record["authkey"]):
        return "Channel is not healthy", 400

    update_channel = Channel.query.filter_by(endpoint=record["endpoint"]).first()

    # Update channel if it already exists
    if update_channel:
        update_channel.name = record["name"]
        update_channel.HUB_AUTHKEY = record["authkey"]
        update_channel.active = False
        db.session.commit()
        if not health_check(record["endpoint"], record["authkey"]):
            return "Channel is not healthy", 400
        return jsonify(created=False, id=update_channel.id), 200
    else:
        channel = Channel(
            name=record["name"],
            endpoint=record["endpoint"],
            authkey=record["authkey"],
            last_heartbeat=datetime.datetime.now(),
            active=True,
        )
        db.session.add(channel)
        db.session.commit()

        return jsonify(created=True, id=channel.id), 200


@app.route("/channels", methods=["GET"])
def get_channels() -> tuple[str, int]:
    """Returns a list of channels.

    Returns:
        (tuple[str, int]): A tuple containing the response message and the status code.
    """

    channels = Channel.query.all()

    return (
        jsonify(
            channels=[
                {"name": c.name, "endpoint": c.endpoint, "authkey": c.authkey}
                for c in channels
            ]
        ),
        200,
    )


# Start development web server
if __name__ == "__main__":
    app.run(port=5555, debug=True)
