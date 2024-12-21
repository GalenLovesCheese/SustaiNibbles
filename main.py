import os
import logging
# import mysql.connector
from telegram import Update 
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
TOKEN = os.getenv('TOKEN')
print(TOKEN)

# # MySQL Database Connection
# connection = mysql.connector.connect(
#     host=os.getenv('DB_HOST'),
#     user=os.getenv('DB_USER'),
#     password=os.getenv('DB_PASSWORD'),
#     database=os.getenv('DB_NAME')
# )
# cursor = connection.cursor()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="hi")

NAME, TYPE = range(2)

# /join function
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Please provide your name:")
    return NAME

async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Thanks! Now provide the type:")
    return TYPE

async def set_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = context.user_data.get("name")
    type_ = update.message.text

    # # Insert data into MySQL database
    # try:
    #     cursor.execute("INSERT INTO user_data (name, type) VALUES (%s, %s)", (name, type_))
    #     connection.commit()
    #     await update.message.reply_text(f"Successfully added name: {name} with type: {type_} to the database!")
    # except mysql.connector.Error as err:
    #     await update.message.reply_text(f"Failed to add data to the database: {err}")

    await update.message.reply_text(f"Received name: {name} and type: {type_} (not saved to the database).")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation canceled.")
    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    #application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Conversation handler for /join
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("join", join)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_name)],
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_type)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()