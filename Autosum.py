import re
import telebot
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# សូមដាក់ BOT_TOKEN ផ្ទាល់ខ្លួនរបស់អ្នកនៅទីនេះ
BOT_TOKEN = "8053556928:AAGDxZzKzh3Fd35Vy1fBMxpQPMzm8iYNNFg"
bot = telebot.TeleBot(BOT_TOKEN)

# ប្រើ Dictionary ដើម្បីរក្សាទុកទិន្នន័យដាច់ដោយឡែកតាម chat_id
transactions = {}

# --- Regex Patterns ---
riel_pattern = re.compile(r"៛([\d,]+)")
usd_pattern = re.compile(r"\$([\d,.]+)")
aba_khr_pattern = re.compile(r"^([\d,]+)\s+paid by.*KHQR", re.IGNORECASE | re.DOTALL)
time_pattern = re.compile(r"\[(.*?)\]")


def create_main_keyboard():
    """បង្កើត Keyboard សម្រាប់បញ្ជា Bot (បានដកប៊ូតុង Today និង Month ចេញ)"""
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    # រក្សាទុកតែប៊ូតុង សរុបទាំងអស់ និង លុបទិន្នន័យ
    btn_all = KeyboardButton("🏦 សរុបទាំងអស់ (All)")
    btn_reset = KeyboardButton("🔄 លុបទិន្នន័យ (Reset)")
    markup.add(btn_all, btn_reset)
    return markup


def parse_transaction(text):
    """វិភាគអត្ថបទដើម្បីស្វែងរកប្រតិបត្តិការ"""
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
            trx_time = datetime.strptime(match_time.group(1), "%m/%d/%Y %I:%M %p")
        except ValueError:
            pass
            
    if currency and amount is not None:
        return {"amount": amount, "currency": currency, "time": trx_time}
    
    return None


def get_summary(chat_id):
    """គណនាផលបូកសរុបនៃប្រតិបត្តិការសម្រាប់ chat_id"""
    user_transactions = transactions.get(chat_id, [])
    
    total_khr = 0
    total_usd = 0
    for t in user_transactions:
        if t["currency"] == "KHR":
            total_khr += t["amount"]
        elif t["currency"] == "USD":
            total_usd += t["amount"]
                
    return total_khr, total_usd

# --- Bot Handlers (ផ្នែកចាត់ការសារ) ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """ចាត់ការ command /start និង /help"""
    welcome_text = (
        "👋 សួស្តី! ខ្ញុំជា Bot សម្រាប់កត់ត្រាចំណាយ។\n\n"
        "👉 **របៀបប្រើប្រាស់:**\n"
        "1. **Forward** សារពីធនាគារ (ABA, ACLEDA) មកកាន់ខ្ញុំ។\n"
        "2. ខ្ញុំនឹងកត់ត្រាចំនួនទឹកប្រាក់ដោយស្វ័យប្រវត្តិ។\n"
        "3. ប្រើប្រាស់ប៊ូតុងខាងក្រោមដើម្បីមើលរបាយការណ៍សរុប។\n\n"
        "សូមបញ្ជូនសារប្រតិបត្តិការរបស់អ្នកឥឡូវនេះ!"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=create_main_keyboard())


@bot.message_handler(commands=['reset'])
def ask_reset(message):
    handle_reset(message)

@bot.message_handler(regexp="🔄 លុបទិន្នន័យ \(Reset\)")
def handle_reset(message):
    """សម្អាតទិន្នន័យប្រតិបត្តិការទាំងអស់សម្រាប់អ្នកប្រើប្រាស់"""
    if message.chat.id in transactions:
        transactions.pop(message.chat.id)
        reply_text = "✅ ទិន្នន័យទាំងអស់របស់អ្នកត្រូវបានលុបចោល។"
    else:
        reply_text = "ℹ️ អ្នកមិនមានទិន្នន័យសម្រាប់លុបទេ។"
    bot.reply_to(message, reply_text, reply_markup=create_main_keyboard())


@bot.message_handler(regexp="🏦 សរុបទាំងអស់ \(All\)")
def summary_all(message):
    khr, usd = get_summary(message.chat.id)
    bot.reply_to(message, f"🏦 សរុបទាំងអស់:\n៛ {khr:,.0f}\n$ {usd:,.2f}")


@bot.message_handler(func=lambda m: True)
def handle_transaction_message(message):
    """Handler ចម្បងសម្រាប់ដំណើរការសារដែលអាចជាប្រតិបត្តិការ"""
    chat_id = message.chat.id
    transaction = parse_transaction(message.text)

    if transaction:
        transactions.setdefault(chat_id, []).append(transaction)
        
        # --- បន្ទាត់ខាងក្រោមនេះត្រូវបានបិទ (Commented out) ---
        #  στόχος: ដើម្បីកុំឱ្យ Bot ផ្ញើសារឆ្លើយតប "បានកត់ត្រា"
        # amount = transaction['amount']
        # currency_symbol = "៛" if transaction['currency'] == 'KHR' else "$"
        # formatted_amount = f"{amount:,.0f}" if transaction['currency'] == 'KHR' else f"{amount:,.2f}"
        # bot.reply_to(message, f"✅ បានកត់ត្រា: {currency_symbol} {formatted_amount}")

        if message.forward_from or message.forward_from_chat:
            try:
                bot.delete_message(chat_id, message.message_id)
            except Exception as e:
                print(f"Could not delete message for chat {chat_id}. Error: {e}")


print("🤖 Bot is running...")
bot.infinity_polling()