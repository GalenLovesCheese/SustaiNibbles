import os
import logging
import mysql.connector
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, ConversationHandler, filters
from dotenv import load_dotenv
import mysql.connector

## initialize the bot, database
load_dotenv()

PASS = os.getenv('PASSWORD')

mydb = mysql.connector.connect(
    host="localhost",
    user="user",
    password = PASS,
    database = "table2" #"sustainibbles"
)

mycursor = mydb.cursor()
mycursor.execute("CREATE DATABASE IF NOT EXISTS table2")
mycursor.execute("CREATE TABLE IF NOT EXISTS Users (User VARCHAR(255), Type VARCHAR(255) CHECK(Type = 'Individual' OR Type = 'Business'))")
mycursor.execute("CREATE TABLE IF NOT EXISTS Announcements (Location VARCHAR(255), Message VARCHAR(255), PAX int)")
mycursor.execute("INSERT INTO Users(User, Type) VALUES('Ben', 'Individual'),('Thomas', 'Individual'),('Margaret', 'Individual'),('Dumping Donuts', 'Business'), ('Ivy Cafe','Business'), ('1793678228', 'Business')")
mycursor.execute("INSERT INTO Announcements(Location, Message, PAX) VALUES('Bukit Panjang', 'Extra rice left over at store, up to 5 people can  take', 5), ('King Albert Park', 'Extra prata remaining', 2), ('Choa Chu Kang', 'Extra chicken remaining', 3)")
mycursor.execute("SELECT * FROM Users") 
  
# fetch all the matching rows  
usr = mycursor.fetchall() 
  
# loop through the rows 
print("Users Table:")
for row in usr: 
    print(row)

mycursor.execute("SELECT * FROM Announcements") 
  
# fetch all the matching rows  
ann = mycursor.fetchall() 
  
# loop through the rows 
print("Announcements Table:")
for row in ann: 
    print(row)
   
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv('TOKEN')

## define commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    print("DEBUG UID: ", user_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to SustaiNibbles! Run /join to get started!")

# /announce
LOCATION, MESSAGE, PAX = range(3)

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """start announcement conversation, store location"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the location:")
    return LOCATION

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """store the location, ask for the message"""
    context.user_data['location'] = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the description:")
    return MESSAGE

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """store the message, ask for the pax"""
    context.user_data['message'] = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the pax:")
    return PAX

async def pax(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """store the pax, add announcement to database"""
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
        print(f"DEBUG: {location}, {message}, {pax}")
        mycursor.execute("INSERT INTO Announcements (Location, Message, PAX) VALUES (%s, %s, %s)", (location, message, pax))
        mycursor.execute("SELECT * FROM Announcements") 
  
        # fetch all the matching rows  
        ann = mycursor.fetchall() 
        
        # loop through the rows 
        print("Announcements Table:")
        for row in ann: 
            print(row)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Announcement has been made!")
        
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You do not have permission to use this command.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Announcement cancelled.")
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))

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
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()