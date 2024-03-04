# Flask Movie Recommender

This project is a distributed messageboard built with flask. It is designed to function with the other channels from all participants of the university course. Our channels consist of a simple "just chatting" channel and a chatbot channel. The chatbot is built with rasa and can do all sorts of tasks from simple chatting to rolling a die or telling the weather for a specific location.


## Showcase

![MessageBoard](https://github.com/GerritBartels/AIandTheWeb/assets/64156238/1ba6b877-e3dc-4740-b94e-c4f82c876e24)


## Features

- A modern, dark-themed chat UI
- A just chatting channel
- A chatbot channel with a rasa-based chatbot. Abilities include:
    - Simple chatting
    - Rolling a die
    - Flipping a coin
    - Telling the current time and date
    - Telling a joke, quote, or fact
    - Recommending a recipe to cook
    - Telling the weather for a specific location
- A hub to manage all channels
- A client to connect to the hub and chat with the channels
- A database to store the chat history depending on the selected user
- Ability to add new users


## Usage

1. Clone the repository. 
2. Change directory: `cd DistributedMessageboard`
3. Set up two virtual environments and install the required dependencies, respectively:
    3.1 Install the required dependencies for the flask apps: `pip install -r requirements.txt`
    3.2 Install the required dependencies for rasa: `pip install -r requirements_rasa.txt`
4. Activate the flask virtual environment.
5. Instantiate the chat database: `flask --app client.py initdb`
6. Start the hub in a dedicated terminal: `python hub.py`
7. Start the just chatting channel in a dedicated terminal: `python just_chatting.py`
8. Register the just chatting channel with the hub: `flask --app user_channel.py register`
9. Start the chatbot channel in a dedicated terminal: `python chatbot.py`
10. Register the chatbot channel with the hub: `flask --app rasa_channel.py register`
11. Start the client in a dedicated terminal: `python client.py`
12. Navigate to the rasa directory: `cd rasa`
13. Activate the rasa virtual environment.
14. Start the rasa server in a dedicated terminal: `rasa run --enable-api --cors "*" --port 5054`
15. Start the rasa action server in a dedicated terminal: `rasa run actions`
16. Open the client in your browser and start chatting.

