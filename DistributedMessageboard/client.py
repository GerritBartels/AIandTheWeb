from flask import Flask, request, render_template, url_for, redirect
import requests
import urllib.parse
import datetime

app = Flask(__name__)

HUB_AUTHKEY = '1234567890'
HUB_URL = 'http://localhost:5555'

CHANNELS = None
LAST_CHANNEL_UPDATE = None


def update_channels():
    global CHANNELS, LAST_CHANNEL_UPDATE
    if CHANNELS and LAST_CHANNEL_UPDATE and (datetime.datetime.now() - LAST_CHANNEL_UPDATE).seconds < 60:
        return CHANNELS
    # fetch list of channels from server
    response = requests.get(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY})
    if response.status_code != 200:
        return "Error fetching channels: "+str(response.text), 400
    channels_response = response.json()
    if not 'channels' in channels_response:
        return "No channels in response", 400
    CHANNELS = channels_response['channels']
    LAST_CHANNEL_UPDATE = datetime.datetime.now()
    return CHANNELS


@app.route('/')
def home_page():
    # fetch list of channels from server
    return render_template("home.html", channels=update_channels())


@app.route('/show')
def show_channel():
    # fetch list of messages from channel
    show_channel = request.args.get('channel', None)
    if not show_channel:
        return "No channel specified", 400
    channel = None
    for c in update_channels():
        if c['endpoint'] == urllib.parse.unquote(show_channel):
            channel = c
            break
    if not channel:
        return "Channel not found", 404
    response = requests.get(channel['endpoint'], headers={'Authorization': 'authkey ' + channel['authkey']})
    if response.status_code != 200:
        return "Error fetching messages: "+str(response.text), 400
    messages = response.json()
    return render_template("channel.html", channel=channel, messages=messages)


@app.route('/post', methods=['POST'])
def post_message():
    # send message to channel
    post_channel = request.form['channel']
    if not post_channel:
        return "No channel specified", 400
    channel = None
    for c in update_channels():
        if c['endpoint'] == urllib.parse.unquote(post_channel):
            channel = c
            break
    if not channel:
        return "Channel not found", 404
    message_content = request.form['content']
    message_sender = request.form['sender']
    message_timestamp = datetime.datetime.now().isoformat()
    response = requests.post(channel['endpoint'],
                             headers={'Authorization': 'authkey ' + channel['authkey']},
                             json={'content': message_content, 'sender': message_sender, 'timestamp': message_timestamp})
    if response.status_code != 200:
        return "Error posting message: "+str(response.text), 400
    return redirect(url_for('show_channel')+'?channel='+urllib.parse.quote(post_channel))


# Start development web server
if __name__ == '__main__':
    app.run(port=5005, debug=True)
