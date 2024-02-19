import json
import requests
import werkzeug
from typing import Union
from flask import Flask, request, jsonify


class ConfigClass(object):
    """Flask application config"""

    # Flask settings
    SECRET_KEY = "This is an INSECURE secret!! DO NOT use this in production!!"


# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + ".ConfigClass")
app.app_context().push()

HUB_URL = "http://localhost:5555"
HUB_AUTHKEY = "1234567890"
CHANNEL_AUTHKEY = "0987654321"
CHANNEL_NAME = "The One and Only Channel"
PORT = 5001
CHANNEL_ENDPOINT = f"http://localhost:{PORT}"
CHANNEL_FILE = "messages.json"


@app.cli.command("register")
def register_command() -> None:
    """Register the channel with the hub."""

    global CHANNEL_AUTHKEY, CHANNEL_NAME, CHANNEL_ENDPOINT

    response = requests.post(
        HUB_URL + "/channels",
        headers={"Authorization": "authkey " + HUB_AUTHKEY},
        data=json.dumps(
            {
                "name": CHANNEL_NAME,
                "endpoint": CHANNEL_ENDPOINT,
                "authkey": CHANNEL_AUTHKEY,
            }
        ),
    )

    if response.status_code != 200:
        print("Error creating channel: " + str(response.status_code))
        return


def check_authorization(request: werkzeug.local.LocalProxy) -> bool:
    """Check if the request is authorized.

    Arguments:
        request (werkzeug.local.LocalProxy): The request object.

    Returns:
        (bool): True if the request is authorized, False otherwise.
    """

    global CHANNEL_AUTHKEY

    # Check if Authorization header is present
    if "Authorization" not in request.headers:
        return False

    # Check if authorization header is valid
    if request.headers["Authorization"] != "authkey " + CHANNEL_AUTHKEY:
        return False

    return True


@app.route("/health", methods=["GET"])
def health_check() -> tuple[str, int]:
    """Check if the channel is healthy.

    Returns:
        (tuple[str, int]): A tuple containing the response message and the status code.
    """

    global CHANNEL_NAME

    if not check_authorization(request):
        return "Invalid authorization", 400

    return jsonify({"name": CHANNEL_NAME}), 200


@app.route("/", methods=["GET"])
def home_page() -> Union[tuple[str, int], str]:
    """Return list of messages.

    Returns:
        (Union[tuple[str, int], str]): A tuple containing the response message and the status code, or the stored messages.
    """

    if not check_authorization(request):
        return "Invalid authorization", 400

    return jsonify(read_messages())


@app.route("/", methods=["POST"])
def send_message() -> tuple[str, int]:
    """Send a message.

    Returns:
        (tuple[str, int]): A tuple containing the response message and the status code.
    """

    required_keys = ["content", "sender", "timestamp"]

    # Check authorization header
    if not check_authorization(request):
        return "Invalid authorization", 400

    # Check if message is present
    message = request.json
    if not message:
        return "No message", 400

    for key in required_keys:
        if key not in message:
            return f"No {key}", 400

    # Add message to messages
    messages = read_messages()
    messages.append(
        {
            "content": message["content"],
            "sender": message["sender"],
            "timestamp": message["timestamp"],
        }
    )

    save_messages(messages)

    return "OK", 200


def read_messages() -> list[dict]:
    """Read the stored messages.

    Returns:
        messages (list[dict]): The stored messages.
    """

    global CHANNEL_FILE

    try:
        f = open(CHANNEL_FILE, "r")
    except FileNotFoundError:
        return []
    try:
        messages = json.load(f)
    except json.decoder.JSONDecodeError:
        messages = []
    f.close()

    return messages


def save_messages(messages: list[dict]) -> None:
    """Save the messages to the file.

    Arguments:
        messages (list[dict]): The messages to save.
    """

    global CHANNEL_FILE

    with open(CHANNEL_FILE, "w") as f:
        json.dump(messages, f)


# Start development web server
if __name__ == "__main__":
    app.run(port=PORT, debug=True)
