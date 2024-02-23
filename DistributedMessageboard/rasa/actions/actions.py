# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
import random
import requests
from datetime import datetime
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, AllSlotsReset
from rasa_sdk.executor import CollectingDispatcher


class ActionWeather(Action):
    def name(self) -> Text:
        return "action_weather"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        city = tracker.get_slot("city")
        
        # Api call to OpenWeathers One Call API
        api_key = "YOUR_API_KEY"
        r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric")
        
        if r.status_code != 200:
            dispatcher.utter_message(f"Sorry, I couldn't find the weather for {city}. Please try again.")

        else:
            data = r.json()
            temp = data['main']['temp']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            description = data['weather'][0]['description']

            response = f"It is currently {temp} degrees in {city} with {description}, the humidity is {humidity}% and the wind speed is {wind_speed} m/s."

            dispatcher.utter_message(response)

        return []
    

class ActionResetAllSlots(Action):

    def name(self):
        return "action_reset_all_slots"

    def run(self, dispatcher, tracker, domain):
        return [AllSlotsReset()]
    

class ActionCoinFlip(Action):

    def name(self):
        return "action_coin_flip"

    def run(self, dispatcher, tracker, domain):
        coin = random.choice(["heads", "tails"])
        dispatcher.utter_message(f"I flipped a coin and it landed on {coin}.")
        return []
    

class ActionRollDice(Action):

    def name(self):
        return "action_dice_roll"

    def run(self, dispatcher, tracker, domain):
        dice = random.choice([1, 2, 3, 4, 5, 6])
        dispatcher.utter_message(f"I rolled a dice and it landed on {dice}.")
        return []
    

class ActionTime(Action):

    def name(self):
        return "action_time"

    def run(self, dispatcher, tracker, domain):
        r = requests.get("http://worldtimeapi.org/api/timezone/Europe/Berlin")
        data = r.json()
        time = data['datetime']
        datetime_object = datetime.fromisoformat(time)
        formatted_time = datetime_object.strftime("%B %d, %Y, %H:%M:%S")
        dispatcher.utter_message(f"The current time in Germany is {formatted_time}.")
        return []
    

class ActionJoke(Action):
    
        def name(self):
            return "action_joke"
    
        def run(self, dispatcher, tracker, domain):
            r = requests.get("https://official-joke-api.appspot.com/jokes/random")
            data = r.json()
            joke = data['setup'] + " " + data['punchline']
            dispatcher.utter_message(joke)
            return []
        

class ActionQuote(Action):
    
        def name(self):
            return "action_quote"
    
        def run(self, dispatcher, tracker, domain):
            r = requests.get("https://api.quotable.io/random")
            data = r.json()
            quote = data['content'] + " - " + data['author']
            dispatcher.utter_message(quote)
            return []
        

class ActionFact(Action):
        
            def name(self):
                return "action_fact"
        
            def run(self, dispatcher, tracker, domain):
                r = requests.get("https://useless-facts.sameerkumar.website/api")
                data = r.json()
                fact = data['data']
                dispatcher.utter_message(fact)
                return []
            

class ActionRecipe(Action):
    
        def name(self):
            return "action_recipe"
    
        def run(self, dispatcher, tracker, domain):
            r = requests.get("https://www.themealdb.com/api/json/v1/1/random.php")
            data = r.json()
            recipe = data['meals'][0]
            name = recipe['strMeal']
            category = recipe['strCategory']
            area = recipe['strArea']
            instructions = recipe['strInstructions']
            ingredients = []
            for i in range(1, 21):
                ingredient = recipe[f'strIngredient{i}']
                if ingredient:
                    ingredients.append(ingredient)
            ingredients = ", ".join(ingredients)
            response = f"Here is a random recipe for you: {name}, a {category} from {area}. {instructions} The ingredients are: {ingredients}."
            dispatcher.utter_message(response)
            return []
        