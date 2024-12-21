import os
import logging
import mysql.connector
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from dotenv import load_dotenv
import mysql.connector

## initialize the bot, database
load_dotenv()

PASS = os.getenv('PASSWORD')

mydb = mysql.connector.connect(
    host="localhost",
    user="user",
    password = PASS,
    database = "sustainibbles"
)

mycursor = mydb.cursor()
mycursor.execute("CREATE DATABASE sustainibbles")
mycursor.execute("CREATE TABLE Users (User VARCHAR(255), Type VARCHAR(255) CHECK(Type = 'Individual' OR Type = 'Business'))")
mycursor.execute("CREATE TABLE Announcements (Location VARCHAR(255), Message VARCHAR(255), PAX int)")
mycursor.execute("INSERT INTO Users(User, Type) VALUES('Ben', 'Individual'),('Thomas', 'Individual'),('Margaret', 'Individual'),('Dumping Donuts', 'Business'), ('Ivy Cafe','Business')")
mycursor.execute("INSERT INTO Announcements(Location, Message, PAX) VALUES('Bukit Panjang', 'Extra rice left over at store, up to 5 people can  take', 5), ('King Albert Park', 'Extra prata remaining', 2), ('Choa Chu Kang', 'Extra chicken remaining', 3)")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

db = mysql.connector.connect(
  host="localhost",
  user="yourusername",
  password="yourpassword",
  database="mydatabase"
)

cursor = db.cursor()

TOKEN = os.getenv('TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to Sustainibles! Run /join to get started!")

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """BUSINESS: Announce details of food surplus\nFormat:\nLOCATION: <location>\nMESSAGE: <message>\nPAX: <pax>"""
    message = update.message.text
    user_id = update.effective_user.id
    
    cursor.execute("SELECT * FROM users where username == %s", user_id)
    result = cursor.fetchone()

    if result and result['role'] == "business":
        location = message.split("LOCATION: ")[1].split("\n")[0]
        message = message.split("MESSAGE: ")[1].split("\n")[0]
        pax = message.split("PAX: ")[1].split("\n")[0]
        
        cursor.execute("INSERT INTO announcements (location, message, pax) VALUES (%s, %s, %s)", (location, message, pax))
        
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Announcement has been made!")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You do not have permission to use this command.")

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
    application.add_handler(CommandHandler("announce", announce))

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