import os
import logging
import mysql.connector
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, ConversationHandler, filters
from dotenv import load_dotenv
import mysql.connector

## initialize the bot, database
load_dotenv()

PASS = os.getenv('PASSWORD')

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password = PASS,
    database = "table3" #"sustainibbles"
)

mycursor = mydb.cursor()
#Executes database code if doesn't exist yet
mycursor.execute("SHOW DATABASES")
databases = mycursor.fetchall()
databaseExists = False
for database in databases:
    if 'table3' in database:
        databaseExists = True
        break

if databaseExists: #== False:
    #mycursor.execute("CREATE DATABASE table3")
    #mycursor.execute("CREATE TABLE Users (Name VARCHAR(255), Type VARCHAR(255) CHECK(Type = 'Individual' OR Type = 'Business'))")
    #mycursor.execute("CREATE TABLE Announcements (Location VARCHAR(255), Message VARCHAR(255), PAX int)")
    mycursor.execute("INSERT INTO Users(Name, Type) VALUES('Ben', 'Individual'),('Thomas', 'Individual'),('Margaret', 'Individual'),('Dumping Donuts', 'Business'), ('Ivy Cafe','Business'), ('1793678228', 'Business')")
    mycursor.execute("INSERT INTO Announcements(Location, Message, PAX) VALUES('Bukit Panjang', 'Extra rice left over at store, up to 5 people can  take', 5), ('King Albert Park', 'Extra prata remaining', 2), ('Choa Chu Kang', 'Extra chicken remaining', 3), ('Bukit Panjang', 'Skibidi balls', 2)")

  
# loop through the rows 
print("Users Table:")
mycursor.execute("SELECT * FROM Users") 
usr = mycursor.fetchall() 
print("Users Table:")
for row in usr: 
    print(row)

mycursor.execute("SELECT * FROM Announcements") 
ann = mycursor.fetchall() 
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
    """Get information about SustaiNibbles initiative"""
    user_id = str(update.effective_user.id)
    print("DEBUG UID: ", user_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to SustaiNibbles! Run /join to get started!")


REGION, NEIGHBOURHOOD, MESSAGE, PAX = range(4)
regions = {
    "North": ["Sembawang", "Woodlands", "Yishun"],
    "North-East": ["Ang Mo Kio", "Hougang", "Punggol", "Sengkang", "Serangoon"],
    "East": ["Bedok", "Pasir Ris", "Tampines"],
    "West": ["Bukit Batok", "Bukit Panjang", "Choa Chu Kang", "Clementi", "Jurong East", "Jurong West", "Tengah"],
    "Central": ["Bishan", "Bukit Merah", "Bukit Timah", "Central Area", "Geylang", "Kallang/Whampoa", "Marine Parade", "Queenstown", "Toa Payoh"]
    }

async def location_constructor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Helper function for location selection: /nearby, /announce"""
    regions_info = ""
    for key, values in regions.items():
        regions_info += f"{key.upper()}:\n"
        for value in values:
            regions_info += f"{value}\n"
        regions_info += "\n"
        
    await context.bot.send_message(chat_id=update.effective_chat.id, text=regions_info)

    region_buttons = [["North", "North-East"], ["East", "West"], ["Central"]]
    reply_markup = ReplyKeyboardMarkup(region_buttons, one_time_keyboard=True, resize_keyboard=True)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please select a general region to proceed:",
        reply_markup=reply_markup
    )
    return REGION


async def region_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    selected_region = update.message.text

    if selected_region in regions:
        context.user_data['selected_region'] = selected_region
        neighbourhoods = regions[selected_region]
        neighbourhood_buttons = [[neighbourhood] for neighbourhood in neighbourhoods]
        reply_markup = ReplyKeyboardMarkup(neighbourhood_buttons, one_time_keyboard=True, resize_keyboard=True)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Great! Please select a neighbourhood within {selected_region}:",
            reply_markup=reply_markup
        )
        return NEIGHBOURHOOD
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Invalid region. Please try again."
        )
        return REGION

async def neighbourhood_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_neighbourhood = update.message.text
    selected_region = context.user_data.get('selected_region')

    if selected_region and selected_neighbourhood in regions[selected_region]:
        context.user_data['selected_neighbourhood'] = selected_neighbourhood
        print("DEBUG:: CTX USER DATA CMD: ", context.user_data.get('command'))
        if context.user_data.get('command') == 'announce':
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"You have selected {selected_neighbourhood} in the {selected_region} region.\nPlease enter the announcement details"
            )
            return MESSAGE
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"You have selected {selected_neighbourhood} in the {selected_region} region."
            )
            mycursor.execute(
            "SELECT Location, Message, PAX FROM Announcements WHERE Location = %s", 
            (selected_neighbourhood,)
            )
            announcements = mycursor.fetchall()
            if announcements == []:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"There are no announcements currently for \n{selected_neighbourhood}"
                )
            else:
                for announcement in announcements:
                    announcementBubble = ""
                    for field in announcement:
                        announcementBubble += str(field) + "\n"
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"Placeholder date:\n{announcementBubble}"
                    )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Something went wrong. Please start over."
        )
    return ConversationHandler.END
#end helper

## GALEN NEARBY HERE; EXMAPLE BC ND CTX FOR ANNOUNCEMENTS
# /nearby
async def nearby(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the nearby conversation."""
    context.user_data['command'] = 'nearby'
    return await location_constructor(update, context)

# /announce
async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """start announcement conversation"""
    context.user_data['command'] = 'announce'
    print("DEBUG: Starting announce command")
    return await location_constructor(update, context)

# async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """store the location, ask for the message"""
#     #context.user_data['location'] = update.message.text
#     await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the description:")
#     return MESSAGE

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """store the message, ask for the pax"""
    context.user_data['message'] = update.message.text
    print(f"DEBUG: Message received: {context.user_data['message']}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the pax:")
    return PAX

async def pax(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """store the pax, add announcement to database"""
    context.user_data['pax'] = update.message.text
    user_id = str(update.effective_user.id)
    print("DEBUG UID: ", user_id)
    
    mycursor.execute("SELECT * FROM Users WHERE Name=%s AND Type=%s", (user_id, 'Business'))
    result = mycursor.fetchall()
    print("DEBUG: ", result)
    
    if result:
        location = context.user_data['selected_neighbourhood']
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
# end /announce

# /nearby



async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel ongoing operation"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Operation cancelled.")
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('announce', announce),
            CommandHandler('nearby', nearby)
        ],
        states={
            REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, region_selected)],
            NEIGHBOURHOOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, neighbourhood_selected)],
            MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, message)],
            PAX: [MessageHandler(filters.TEXT & ~filters.COMMAND, pax)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(conv_handler)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()