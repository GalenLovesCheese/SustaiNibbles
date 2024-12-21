import os
import logging
import mysql.connector
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import mysql.connector

## initialize the bot, database
load_dotenv()

PASS = os.getenv('PASSWORD')

mydb = mysql.connector.connect(
    host="localhost",
    user="user",
    password = PASS,
    database = "table1"
)

mycursor = mydb.cursor()
#mycursor.execute("CREATE DATABASE table1")
# mycursor.execute("CREATE TABLE Users (User VARCHAR(255), Type VARCHAR(255) CHECK(Type = 'Individual' OR Type = 'Business'))")
# mycursor.execute("CREATE TABLE Announcements (Location VARCHAR(255), Message VARCHAR(255), PAX int)")
mycursor.execute("INSERT INTO Users(User, Type) VALUES('Ben', 'Individual'),('Thomas', 'Individual'),('Margaret', 'Individual'),('Dumping Donuts', 'Business'), ('Ivy Cafe','Business'), ('1793678228', 'Business')")
mycursor.execute("INSERT INTO Announcements(Location, Message, PAX) VALUES('Bukit Panjang', 'Extra rice left over at store, up to 5 people can  take', 5), ('King Albert Park', 'Extra prata remaining', 2), ('Choa Chu Kang', 'Extra chicken remaining', 3)")
# mycursor.execute("INSERT INTO Users(User, Type) VALUES('Ben', 'Individual'),('Thomas', 'Individual'),('Margaret', 'Individual'),('Dumping Donuts', 'Business'), ('Ivy Cafe','Business')")
# mycursor.execute("INSERT INTO Announcements(Location, Message, PAX) VALUES('Bukit Panjang', 'Extra rice left over at store, up to 5 people can  take', 5), ('King Albert Park', 'Extra prata remaining', 2), ('Choa Chu Kang', 'Extra chicken remaining', 3)")

# execute your query 
mycursor.execute("SELECT * FROM Users") 
  
# fetch all the matching rows  
result = mycursor.fetchall() 
  
# loop through the rows 
print("Users Table:")
for row in result: 
    print(row)
    print("")
   
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv('TOKEN')

## define commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to Sustainibles! Run /join to get started!")

# Define states
LOCATION, MESSAGE, PAX = range(3)

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the announcement conversation."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the location:")
    return LOCATION

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store the location and ask for the message."""
    context.user_data['location'] = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the description:")
    return MESSAGE

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store the message and ask for the pax."""
    context.user_data['message'] = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the pax:")
    return PAX

async def pax(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store the pax and make the announcement."""
    context.user_data['pax'] = update.message.text
    user_id = str(update.effective_user.id)
    print("DEBUG UID: ", user_id)
    
    mycursor.execute("SELECT * FROM Users WHERE User=%s AND Type=%s", (user_id, 'Business'))
    result = mycursor.fetchall()
    print("DEBUG: ", result)
    
    if result:
        location = context.user_data['location']
        message = context.user_data['message']
        pax = context.user_data['pax']
        print("DEBUG: %s; %s; %s", location, message, pax)
        mycursor.execute("INSERT INTO announcements (Location, Message, PAX) VALUES (%s, %s, %s)", (location, message, pax))
        
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Announcement has been made!")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You do not have permission to use this command.")
    return ConversationHandler.END



def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("announce", announce))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('announce', announce)],
        states={
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location)],
            MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, message)],
            PAX: [MessageHandler(filters.TEXT & ~filters.COMMAND, pax)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # on non command i.e message - echo the message on Telegram
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()