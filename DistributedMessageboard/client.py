import requests
import datetime
import urllib.parse
from typing import Union
from flask import Flask, request, render_template, url_for, redirect

app = Flask(__name__)

HUB_AUTHKEY = "1234567890"
HUB_URL = "http://localhost:5555"

CHANNELS = None
LAST_CHANNEL_UPDATE = None


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
        channel["endpoint"], headers={"Authorization": "authkey " + channel["authkey"]}
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

    return render_template("home.html", channels=update_channels())


@app.route("/show")
def show_channel() -> Union[tuple[str, int], str]:
    """Return list of messages for a channel.

    Returns:
        (Union[tuple[str, int], str]): A tuple containing the response message and the status code,
            or the rendered channel page.
    """
    channel_name = request.args.get("channel", None)

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

    return render_template("channel.html", channel=channel, messages=messages)


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

    return render_template("channel.html", channel=channel, messages=messages)


# Start development web server
if __name__ == "__main__":
    app.run(port=5005, debug=True)
