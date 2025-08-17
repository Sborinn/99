import re
import os
import json
import telebot
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# --- Configuration ---

# 1. Securely get the token from an environment variable.
#    The string inside getenv() must be the NAME of the variable, not the token itself.
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Error: BOT_TOKEN environment variable not set.")

bot = telebot.TeleBot(BOT_TOKEN)
DATA_FILE = "transactions.json"

# --- Data Persistence Functions ---

def load_data():
    """Loads transaction data from the JSON file."""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            # Convert string keys from JSON back to integer keys for chat_id
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is empty, start with an empty dictionary
        return {}

def save_data(data):
    """Saves transaction data to the JSON file."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, default=str)

# Load existing data when the bot starts
transactions = load_data()


# --- Regex Patterns ---
riel_pattern = re.compile(r"៛([\d,]+)")
usd_pattern = re.compile(r"\$([\d,.]+)")
aba_khr_pattern = re.compile(r"^([\d,]+)\s+paid by.*KHQR", re.IGNORECASE | re.DOTALL)
time_pattern = re.compile(r"\[(.*?)\]")


def create_main_keyboard():
    """Creates the main reply keyboard."""
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_all = KeyboardButton("🏦 សរុបទាំងអស់ (All)")
    btn_clear = KeyboardButton("🗑️ សម្អាត (Clear)")
    
    # The "Reset" button has been removed.
    markup.add(btn_all, btn_clear) 
    return markup


def parse_transaction(text):
    """Parses text to find a transaction, returning a dictionary or None."""
    currency, amount = None, None
    trx_time = datetime.now()

    match_aba_khr = aba_khr_pattern.search(text)
    if match_aba_khr:
        amount_str = match_aba_khr.group(1).replace(",", "")
        amount = int(amount_str)
        currency = "KHR"
    else:
        match_riel = riel_pattern.search(text)
        if match_riel:
            amount_str = match_riel.group(1).replace(",", "")
            amount = int(amount_str)
            currency = "KHR"
        elif usd_pattern.search(text):
            match_usd = usd_pattern.search(text)
            amount_str = match_usd.group(1).replace(",", "")
            amount = float(amount_str)
            currency = "USD"

    match_time = time_pattern.search(text)
    if match_time:
        try:
            # Attempt to parse the timestamp from the message
            trx_time = datetime.strptime(match_time.group(1), "%m/%d/%Y %I:%M %p")
        except ValueError:
            # If parsing fails, use the current time
            pass

    if currency and amount is not None:
        return {"amount": amount, "currency": currency, "time": trx_time.isoformat()}

    return None


def get_summary(chat_id):
    """Calculates the total sum of transactions for a specific user."""
    user_transactions = transactions.get(chat_id, [])

    total_khr = sum(t["amount"] for t in user_transactions if t["currency"] == "KHR")
    total_usd = sum(t["amount"] for t in user_transactions if t["currency"] == "USD")

    return total_khr, total_usd

# --- Bot Handlers ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Handles /start and /help commands."""
    welcome_text = (
        "👋 សួស្តី! ខ្ញុំជា Bot សម្រាប់កត់ត្រាចំណូល។\n\n"
        "👉 **របៀបប្រើប្រាស់:**\n"
        "1. **Forward** សារពីធនាគារ (ABA, ACLEDA) មកកាន់ខ្ញុំ។\n"
        "2. ខ្ញុំនឹងកត់ត្រាចំនួនទឹកប្រាក់ដោយស្វ័យប្រវត្តិ។\n"
        "3. ប្រើប្រាស់ប៊ូតុងខាងក្រោមដើម្បីមើលរបាយការណ៍សរុប។\n\n"
        "សូមបញ្ជូនសារប្រតិបត្តិការរបស់អ្នកឥឡូវនេះ!"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=create_main_keyboard())


# ===== The "handle_reset" function has been removed. =====


@bot.message_handler(regexp=r"🏦 សរុបទាំងអស់ \(All\)")
def summary_all(message):
    """Provides a summary of all recorded transactions."""
    khr, usd = get_summary(message.chat.id)
    bot.reply_to(message, f"🏦 សរុបទាំងអស់:\n៛ {khr:,.0f}\n$ {usd:,.2f}")


@bot.message_handler(regexp=r"🗑️ សម្អាត \(Clear\)")
def handle_clear(message):
    """'Clears' the screen by re-sending the welcome message."""
    # Note: A bot cannot truly delete the entire chat history for a user.
    # This function provides a clean slate by re-sending the main menu.
    try:
        # First, delete the user's command message (e.g., "🗑️ សម្អាត (Clear)")
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        # It might fail if the bot doesn't have delete permissions, so we print and continue.
        print(f"Could not delete message {message.message_id} in chat {message.chat.id}. Error: {e}")
    
    # Then, send a fresh welcome message to create a 'clean' starting point.
    send_welcome(message)


@bot.message_handler(func=lambda m: True)
def handle_transaction_message(message):
    """Main handler to process potential transaction messages."""
    chat_id = message.chat.id
    transaction = parse_transaction(message.text)

    if transaction:
        # Add the new transaction and save the updated data
        transactions.setdefault(chat_id, []).append(transaction)
        save_data(transactions)

        # Automatically delete the forwarded message for privacy and cleanliness
        if message.forward_from or message.forward_from_chat:
            try:
                bot.delete_message(chat_id, message.message_id)
            except Exception as e:
                print(f"Could not delete message for chat {chat_id}. Error: {e}")
    else:
        # Improved User Experience: Respond to messages that are not transactions or buttons.
        # ===== UPDATED LIST OF BUTTONS =====
        button_texts = ["🏦 សរុបទាំងអស់ (All)", "🗑️ សម្អាត (Clear)"]
        if message.text not in button_texts:
            bot.reply_to(message, "🤔 ខ្ញុំមិនយល់សារនេះទេ។ សូមបញ្ជូនសារប្រតិបត្តិការពីធនាគារ។\n(I didn't understand that. Please forward a transaction message.)")


# --- Start the Bot ---
print("🤖 Bot is running...")
bot.infinity_polling()
