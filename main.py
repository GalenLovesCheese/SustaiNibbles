import os
import logging
import mysql.connector
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

PASS = os.getenv('PASSWORD')

mydb = mysql.connector.connect(
    host="localhost",
    user="user",
    password = PASS,
    database = "sustainibbles"
)

mycursor = mydb.cursor()
mycursor.execute("INSERT INTO Users(User, Type) VALUES('Ben', 'Individual'),('Thomas', 'Individual'),('Margaret', 'Individual'),('Dumping Donuts', 'Business'), ('Ivy Cafe','Business')")
mycursor.execute("INSERT INTO Announcements(Location, Message, PAX) VALUES('Bukit Panjang', 'Extra rice left over at store, up to 5 people can  take', 5), ('King Albert Park', 'Extra prata remaining', 2), ('Choa Chu Kang', 'Extra chicken remaining', 3)")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
TOKEN = os.getenv('TOKEN')
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="hi")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    #application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()