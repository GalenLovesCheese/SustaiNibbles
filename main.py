import os
import logging
import mysql.connector
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from dotenv import load_dotenv
import mysql.connector

## initialize the bot, database
load_dotenv()

PASS = os.getenv('PASSWORD')

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password = PASS,
    database = "sustainibbles"
)

mycursor = mydb.cursor()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

cursor = mydb.cursor()
#mycursor.execute("CREATE TABLE Users (Name VARCHAR(255), Type VARCHAR(255))")
mycursor.execute("INSERT INTO Users(Name, Type) VALUES('Ben', 'Individual'),('Thomas', 'Individual'),('Margaret', 'Individual'),('Dumping Donuts', 'Business'), ('Ivy Cafe','Business')")
cursor.execute("SELECT * FROM Users")
myresult = cursor.fetchall()
for x in myresult:
    print(x)

TOKEN = os.getenv('TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to Sustainibbles! Run /join to get started!")

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
    await update.message.reply_text("Please provide your Name:")
    return NAME

async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Thanks! Now provide the Type:")
    type_buttons = [["Individual"], ["Business"]]
    reply_markup = ReplyKeyboardMarkup(type_buttons, one_time_keyboard=True, resize_keyboard=True)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please select a type to proceed:",
        reply_markup=reply_markup
    )
    return TYPE

async def set_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = context.user_data.get("name")
    type_i = update.message.text

    # Insert data into MySQL database
    try:
        cursor.execute("INSERT INTO Users (Name, Type) VALUES (%s, %s)", (name, type_i))
        # mydb.commit()
        await update.message.reply_text(f"Successfully added Name: {name} with type: {type_i} to the database!")
    except mysql.connector.Error as err:
        await update.message.reply_text(f"Failed to add data to the database: {err}")

    # await update.message.reply_text(f"Received Name: {name} and Type: {type_i} (not saved to the database).")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled.")
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