import requests
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from threading import Thread, Event

# Global dictionary to store user tokens
user_tokens = {}

# URLs for APIs
base_url = "https://api.farmgo.xyz/miniapps/api/game_cultivation/"
click_url = "https://log.bestchart.xyz/api/event"
increase_capacity_url_sheep = "https://api.farmgo.xyz/miniapps/api/game_cultivation/OutputIncreaseUnitCapacityNowNum?type=3"
increase_capacity_url_cow = "https://api.farmgo.xyz/miniapps/api/game_cultivation/OutputIncreaseUnitCapacityNowNum?type=2"
increase_capacity_url_chicken = "https://api.farmgo.xyz/miniapps/api/game_cultivation/OutputIncreaseUnitCapacityNowNum?type=1"

# Event to control the mining threads
stop_event = Event()

# Function to set the token for a user
def set_token(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if len(context.args) == 1:
        user_tokens[chat_id] = context.args[0]
        update.message.reply_text("Bearer token set successfully!")
    else:
        update.message.reply_text("Please provide a valid Bearer token like this: /token <your-token>")

# Function to get the current token for a user
def get_user_token(chat_id):
    return user_tokens.get(chat_id, None)

# Function to fetch game state data from the API
def get_data(token):
    try:
        headers = {'Authorization': f'Bearer {token}', 'Origin': 'https://app.farmgo.xyz'}
        response = requests.get(base_url + 'Data', headers=headers)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None

def click_animal(animal_type: str, update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    token = get_user_token(chat_id)
    
    if not token:
        update.message.reply_text("Please set your Bearer token first using /token <your-token>.")
        return

    try:
        payload = {
            "n": f"act_{animal_type}_click",
            "u": "your_user_data_here",  # Replace with actual user data
            "d": "app.farmgo.xyz",
            "r": "https://web.telegram.org/"
        }
        headers = {
            'Authorization': f'Bearer {token}',
            'Origin': 'https://app.farmgo.xyz',
            'Content-Type': 'application/json'
        }
        response = requests.post(click_url, headers=headers, json=payload)
        
        if response.status_code == 202:
            specific_count = display_specific_count(animal_type, get_data(token))
            update.message.reply_text(f"{animal_type.capitalize()} clicked successfully! {specific_count}")
            increase_capacity(animal_type, token)
        else:
            update.message.reply_text(f"Failed to click {animal_type}. Status code: {response.status_code}")
    except Exception as e:
        update.message.reply_text(f"Exception occurred while clicking {animal_type}: {e}")

def increase_capacity(animal_type: str, token: str):
    try:
        if animal_type == "sheep":
            increase_capacity_url = increase_capacity_url_sheep
        elif animal_type == "cow":
            increase_capacity_url = increase_capacity_url_cow
        elif animal_type == "chicken":
            increase_capacity_url = increase_capacity_url_chicken
        else:
            return

        headers = {
            'Authorization': f'Bearer {token}',
            'Origin': 'https://app.farmgo.xyz',
            'Content-Type': 'application/json'
        }
        response = requests.post(increase_capacity_url, headers=headers)
        if response.status_code == 200:
            print(f"{animal_type.capitalize()} unit capacity increased successfully!")
        else:
            print(f"Failed to increase {animal_type} unit capacity. Status code: {response.status_code}")
    except Exception as e:
        print(f"Exception occurred while increasing {animal_type} unit capacity: {e}")

def display_specific_count(animal_type: str, data):
    try:
        if 'data' in data and 'output' in data['data']:
            count = 0
            for entry in data['data']['output']:
                if (animal_type == "chicken" and entry['type'] == 1) or \
                   (animal_type == "cow" and entry['type'] == 2) or \
                   (animal_type == "sheep" and entry['type'] == 3):
                    count = entry['unitCapacityNowNum']
            return f"Total {animal_type.capitalize()}s: {count}"
        else:
            return "No game data available."
    except Exception as e:
        return f"Error fetching {animal_type} count: {e}"

def display_counts(data):
    try:
        chicken_count = cow_count = sheep_count = 0
        if 'data' in data and 'output' in data['data']:
            for entry in data['data']['output']:
                if entry['type'] == 1:
                    chicken_count = entry['unitCapacityNowNum']
                elif entry['type'] == 2:
                    cow_count = entry['unitCapacityNowNum']
                elif entry['type'] == 3:
                    sheep_count = entry['unitCapacityNowNum']
        return f"Total Chickens: {chicken_count} | Total Cows: {cow_count} | Total Sheep: {sheep_count}"
    except Exception as e:
        return f"Error displaying counts: {e}"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome to the Farm Bot!")

def show_counts(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    token = get_user_token(chat_id)
    if not token:
        update.message.reply_text("Please set your Bearer token first using /token <your-token>.")
        return

    data = get_data(token)
    counts_message = display_counts(data)
    update.message.reply_text(counts_message)

def mine_animal(animal_type: str, update: Update, context: CallbackContext):
    update.message.reply_text(f"Starting to mine {animal_type}s...")
    while not stop_event.is_set():
        click_animal(animal_type, update, context)
        time.sleep(1)
    update.message.reply_text(f"Stopped mining {animal_type}s.")

def mine_sheep(update: Update, context: CallbackContext):
    stop_event.clear()
    thread = Thread(target=mine_animal, args=("sheep", update, context))
    thread.start()

def mine_cow(update: Update, context: CallbackContext):
    stop_event.clear()
    thread = Thread(target=mine_animal, args=("cow", update, context))
    thread.start()

def mine_chicken(update: Update, context: CallbackContext):
    stop_event.clear()
    thread = Thread(target=mine_animal, args=("chicken", update, context))
    thread.start()

def stop_mining(update: Update, context: CallbackContext):
    stop_event.set()
    update.message.reply_text("Mining stopped.")

def cmds(update: Update, context: CallbackContext):
    commands = "/start\n/show_counts\n/mine_sheep\n/mine_cow\n/mine_chicken\n/stop\n/token\n/cmds\n/states"
    update.message.reply_text(f"Available commands:\n{commands}")

def states(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    token = get_user_token(chat_id)
    if not token:
        update.message.reply_text("Please set your Bearer token first using /token <your-token>.")
        return

    data = get_data(token)
    if data:
        total_coins = data.get('data', {}).get('coins', 'Unknown')
        chickens = cows = sheep = 0
        for entry in data.get('data', {}).get('output', []):
            if entry['type'] == 1:
                chickens += entry['unitCapacityNowNum']
            elif entry['type'] == 2:
                cows += entry['unitCapacityNowNum']
            elif entry['type'] == 3:
                sheep += entry['unitCapacityNowNum']

        message = (f"Total Coins: {total_coins}\n"
                   f"Total Chickens: {chickens}\n"
                   f"Total Cows: {cows}\n"
                   f"Total Sheep: {sheep}")
        update.message.reply_text(message)
    else:
        update.message.reply_text("Failed to fetch game state. Please check your Bearer token.")

def main():
    updater = Updater("5526046435:AAHLOD_32nzw2-m-ChrKWeZu2xeft1S53lI", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("show_counts", show_counts))
    dp.add_handler(CommandHandler("mine_sheep", mine_sheep))
    dp.add_handler(CommandHandler("mine_cow", mine_cow))
    dp.add_handler(CommandHandler("mine_chicken", mine_chicken))
    dp.add_handler(CommandHandler("stop", stop_mining))
    dp.add_handler(CommandHandler("token", set_token))
    dp.add_handler(CommandHandler("cmds", cmds))
    dp.add_handler(CommandHandler("states", states))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
