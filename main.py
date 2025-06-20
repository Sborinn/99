#https://api.telegram.org/bot<8138001996:AAHZk7W_0oE1tCiyMmOaf-o_2sQfmR_WD6g>/setwebhook?url=https://yourapp.onrender.com/webhook/<8138001996:AAHZk7W_0oE1tCiyMmOaf-o_2sQfmR_WD6g>
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8138001996:AAHZk7W_0oE1tCiyMmOaf-o_2sQfmR_WD6g"
ADMIN_CHAT_ID = 7137869037  # ប្ដូរជាមួយ chat_id របស់ UserAdmin

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu_keyboard = [
        ["📋 ព័ត៌មានព្រឹត្តិការណ៍", "💰 បង់ប្រាក់ជាមួយ Admin"],
        ["🐓 ព័ត៌មានមាន់", "🆘 ជំនួយ"]
    ]
    reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🎉 សូមស្វាគមន៍មកកាន់ M99 មាន់ជល់!\n\n📋 សូមជ្រើសរើសម៉ឺនុយខាងក្រោម:",
        reply_markup=reply_markup
    )

# Handle Text Message
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if "បង់ប្រាក់" in text or "deposit" in text:
        reply = (
            "💵 បង់ប្រាក់ជាមួយ Admin\n\n"
            "1️⃣ សូមផ្ទេរប្រាក់ទៅគណនីដែលបានផ្តល់\n"
            "2️⃣ ថត Slip ផ្ទេរប្រាក់\n"
            "3️⃣ ផ្ញើរទៅ Bot នេះ ឬផ្ញើទៅ Admin: @M99_Admin_Support\n\n"
            "✅ ប្រាក់នឹងបញ្ចូលក្នុងគណនីរបស់អ្នកក្នុងរយៈពេល 5-10 នាទី!"
        )
    elif "ព្រឹត្តិការណ៍" in text or "event" in text:
        reply = "📅 ព្រឹត្តិការណ៍ថ្មីៗ:\n- 🐓 Fight Night: ថ្ងៃសៅរ៍\n- 🏆 Champion Series: ថ្ងៃអាទិត្យ"
    elif "មាន់" in text or "chicken" in text:
        reply = "🐓 ប្រភេទមាន់:\n- មាន់ខ្មែរបុរាណ\n- មាន់ថៃ\n\nចង់ដឹងបន្ថែម សូមសួរបានទៀត!"
    elif "ជំនួយ" in text or "help" in text:
        reply = "🆘 សូមទំនាក់ទំនង CS: @M99_CS_Support"
    else:
        reply = "🤖 ខ្ញុំមិនយល់សំណួរនេះទេ។ សូមសួរថ្មី ឬវាយ 'ជំនួយ' ដើម្បីជួយអ្នក។"

    await update.message.reply_text(reply)

# Forward Photo to Admin
async def forward_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        await update.message.reply_text("✅ បានទទួលរូបភាព! กำลังส่งទៅ Admin...")
        await context.bot.forward_message(
            chat_id=ADMIN_CHAT_ID,
            from_chat_id=update.message.chat.id,
            message_id=update.message.message_id
        )
    else:
        await update.message.reply_text("📸 សូមផ្ញើររូបភាពបង្កាន់ដៃ (Transfer Slip)!")

# Run Bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, forward_photo))

    print("🤖 Bot កំពុងដំណើរការ... រង់ចាំភ្ញៀវ...")
    app.run_polling()



