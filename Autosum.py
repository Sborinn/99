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
riel_pattern = re.compile(r"៛\s*([\d,]+)")
usd_pattern = re.compile(r"\$\s*([\d,.]+)")
aba_khr_pattern = re.compile(r"([\d,]+)\s+paid by.*?KHQR", re.IGNORECASE | re.DOTALL)
payway_khr_pattern = re.compile(r"PayWay by ABA.*?៛\s*([\d,]+)\s+paid by", re.IGNORECASE | re.DOTALL)
payway_usd_pattern = re.compile(r"PayWay by ABA.*?\$\s*([\d,.]+)\s+paid by", re.IGNORECASE | re.DOTALL)
time_pattern = re.compile(r"\[(.*?)\]")


def create_main_keyboard():
    """Creates the main reply keyboard."""
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_all = KeyboardButton("🏦 សរុបទាំងអស់ (All)")
    btn_reset = KeyboardButton("🔄 លុបទិន្នន័យ (Reset)")
    
    markup.add(btn_all, btn_reset) 
    return markup


def parse_transactions(text):
    """Parses text to find ALL transactions, sums them by currency, and returns a list of total transactions."""
    total_khr = 0
    total_usd = 0
    trx_time = datetime.now()
    
    remaining_text = text

    match_time = time_pattern.search(text)
    if match_time:
        try:
            trx_time = datetime.strptime(match_time.group(1), "%m/%d/%Y %I:%M %p")
        except ValueError:
            pass 

    payway_khr_matches = payway_khr_pattern.findall(remaining_text)
    for amount_str in payway_khr_matches:
        total_khr += int(amount_str.replace(",", ""))

    payway_usd_matches = payway_usd_pattern.findall(remaining_text)
    for amount_str in payway_usd_matches:
        total_usd += float(amount_str.replace(",", ""))
        
    remaining_text = payway_khr_pattern.sub("", remaining_text)
    remaining_text = payway_usd_pattern.sub("", remaining_text)

    aba_khqr_matches = aba_khr_pattern.findall(remaining_text)
    for amount_str in aba_khqr_matches:
        total_khr += int(amount_str.replace(",", ""))
    remaining_text = aba_khr_pattern.sub("", remaining_text)

    riel_matches = riel_pattern.findall(remaining_text)
    for amount_str in riel_matches:
        total_khr += int(amount_str.replace(",", ""))

    usd_matches = usd_pattern.findall(remaining_text)
    for amount_str in usd_matches:
        total_usd += float(amount_str.replace(",", ""))

    transactions_found = []
    time_iso = trx_time.isoformat()

    if total_khr > 0:
        transactions_found.append({"amount": total_khr, "currency": "KHR", "time": time_iso})
    
    if total_usd > 0:
        transactions_found.append({"amount": total_usd, "currency": "USD", "time": time_iso})

    return transactions_found


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


@bot.message_handler(commands=['reset'])
@bot.message_handler(regexp=r"🔄 លុបទិន្នន័យ \(Reset\)")
def handle_reset(message):
    """Clears all transaction data for the user."""
    if message.chat.id in transactions:
        transactions.pop(message.chat.id)
        save_data(transactions)
        reply_text = "✅ ទិន្នន័យទាំងអស់របស់អ្នកត្រូវបានលុបចោល។"
    else:
        reply_text = "ℹ️ អ្នកមិនមានទិន្នន័យសម្រាប់លុបទេ។"
    
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Could not delete message {message.message_id} in chat {message.chat.id}. Error: {e}")
        
    bot.send_message(message.chat.id, reply_text, reply_markup=create_main_keyboard())


@bot.message_handler(regexp=r"🏦 សរុបទាំងអស់ \(All\)")
def summary_all(message):
    """Provides a summary of all recorded transactions."""
    khr, usd = get_summary(message.chat.id)
    
    # ===== NEW CALCULATION ADDED HERE =====
    # Convert USD to KHR and add to the existing KHR total.
    # The exchange rate is fixed at 4000 KHR per USD.
    total_in_khr = khr + (usd * 4000)

    # ===== SUMMARY TEXT UPDATED with the new total line =====
    summary_text = (
        f"🏦 សរុបទាំងអស់:\n"
        f"`៛ {khr:,.0f}`\n"
        f"`$ {usd:,.2f}`\n"
        f"លុយសរុប `៛ {total_in_khr:,.0f}`"
    )
    
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Could not delete message {message.message_id} in chat {message.chat.id}. Error: {e}")
    
    bot.send_message(message.chat.id, summary_text, parse_mode='Markdown')


@bot.message_handler(func=lambda m: True)
def handle_transaction_message(message):
    """Main handler to process potential transaction messages."""
    chat_id = message.chat.id
    found_transactions = parse_transactions(message.text)

    if found_transactions:
        for trx in found_transactions:
            transactions.setdefault(chat_id, []).append(trx)
        save_data(transactions)

        # Define keywords that identify a detailed bank message.
        is_detailed_message = "paid by" in message.text.lower() or "payway" in message.text.lower()

        # Only delete the message if it's a forwarded message OR a detailed bank message.
        if message.forward_from or message.forward_from_chat or is_detailed_message:
            try:
                bot.delete_message(chat_id, message.message_id)
            except Exception as e:
                print(f"Could not delete message for chat {chat_id}. Error: {e}")
    else:
        button_texts = ["🏦 សរុបទាំងអស់ (All)", "🔄 លុបទិន្នន័យ (Reset)"]
        if message.text not in button_texts:
            bot.reply_to(message, "🤔 ខ្ញុំមិនយល់សារនេះទេ។ សូមបញ្ជូនសារប្រតិបត្តិការពីធនាគារ។\n(I didn't understand that. Please forward a transaction message.)")


# --- Start the Bot ---
print("🤖 Bot is running...")
bot.infinity_polling()
