import os
import logging
import mysql.connector
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, ConversationHandler, filters
from dotenv import load_dotenv

## initialize the bot, database
load_dotenv()
USER = os.getenv('USERNAME')
PASS = os.getenv('PASSWORD')

initialdb = mysql.connector.connect(
    host="localhost",
    user=USER,
    password = PASS,
    #database = "table1"
)

mycursor = initialdb.cursor()
#Checks if database exists, if not, create database structure. Always connects to database at the end
mycursor.execute("SHOW DATABASES")
databases = mycursor.fetchall()
databaseExists = False
for database in databases:
    if 'table1' in database:
        databaseExists = True
        break

if databaseExists == False:
    mycursor.execute("CREATE DATABASE table1")
    mydb = mysql.connector.connect(
        host = "localhost",
        user = USER,
        password = PASS,
        database = "table1"
    )
    mycursor = mydb.cursor()
    mycursor.execute("CREATE TABLE Users (Name VARCHAR(255), Type VARCHAR(255))")
    mycursor.execute("CREATE TABLE Announcements (Location VARCHAR(255), Message VARCHAR(255), PAX int)")
    mycursor.execute("INSERT INTO Users(Name, Type) VALUES('Ben', 'Individual'),('Thomas', 'Individual'),('Margaret', 'Individual'),('Dumping Donuts', 'Business'), ('Ivy Cafe','Business')")
    mydb.commit()
    mycursor.execute("INSERT INTO Announcements(Location, Message, PAX) VALUES('Bukit Panjang', 'Extra rice left over at store, up to 5 people can  take', 5), ('King Albert Park', 'Extra prata remaining', 2), ('Choa Chu Kang', 'Extra chicken remaining', 3)")
    mydb.commit()
else:
    mydb = mysql.connector.connect(
        host = "localhost",
        user = USER,
        password = PASS,
        database = "table1"
    )
    mycursor = mydb.cursor()

  
# loop through the rows 
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
    terms = """
    Welcome to SustaiNibbles 😋! By using this bot, you agree to the following terms and conditions. Please read them carefully before proceeding.  

1. Purpose  
This bot facilitates the sharing of surplus food from businesses to individuals in need, promoting sustainability and reducing food waste.  

2. Eligibility  
Individuals: You must be at least 18 years old to use this bot.  
Businesses: Only verified businesses may register to share surplus food.  

3. Responsibility of Users  
Businesses:  
Ensure that surplus food shared is safe and consumable at the time of notification.  
Provide accurate details about the food, including quantity, type, and pickup time/location.  
Individuals:  
Collect food within the specified timeframe and location provided by businesses.  
Confirm you understand and accept the condition of the food.  

4. Food Safety and Liability  
This bot does not verify the quality, safety, or condition of the food being shared.  
The bot and its creators are not responsible for any adverse effects arising from the consumption of food obtained through this service.  
Food recipients consume the food at their own risk.  

5. Prohibited Use  
Misuse of the bot, including providing false information, harassment, or any illegal activity, is strictly prohibited.  
Businesses must not share expired or hazardous food.  

6. Data Privacy  
The bot collects and uses minimal data required for notifications and interactions.  
We do not share your personal information with third parties without your consent.  

7. Modifications to Terms  
These terms may be updated periodically. Users will be notified of significant changes, and continued use of the bot constitutes acceptance of the updated terms.  

8. Disclaimer of Warranties  
This service is provided “as is” without any warranties, express or implied.  
We do not guarantee uninterrupted or error-free operation of the bot.  

9. Termination of Access  
We reserve the right to suspend or terminate access to the bot for any user who violates these terms.  

10. Governing Law  
These terms and conditions are governed by the laws, without regard to its conflict of law provisions.  

By using this bot, you confirm that you have read, understood, and agree to these terms and conditions.  
    
Run /join to get started!    
"""

    # Send the terms as a message
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=terms
    )

NAME, TYPE = range(2)

# /join function
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Automatically set the user's name as their effective_user.id
    context.user_data["name"] = str(update.effective_user.id)
    type_buttons = [["Individual"], ["Business"]]
    reply_markup = ReplyKeyboardMarkup(type_buttons, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        text="Welcome! Your user ID has been set. Please select whether you are an indiviidual or a business:",
        reply_markup=reply_markup
    )
    return TYPE

async def set_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Retrieve the name and selected type
    name = context.user_data.get("name")
    type_ = update.message.text

    # Validate the type selection
    if type_ not in ["Individual", "Business"]:
        await update.message.reply_text("Invalid selection. Please choose either 'Individual' or 'Business' using the buttons.")
        return TYPE  # Stay in the TYPE state

    # Insert data into MySQL database
    try:
        mycursor.execute("INSERT INTO Users (Name, Type) VALUES (%s, %s)", (name, type_))
        mydb.commit()
        await update.message.reply_text(f"Successfully registered ID: {name} with type: {type_}!")
    except mysql.connector.Error as err:
        await update.message.reply_text(f"Database error: {err}")
    mycursor.execute("SELECT * FROM Users") 
    usr = mycursor.fetchall() 
    print("DEBUG:: JOIN: Users Table:")
    for row in usr: 
        print(row)
    return ConversationHandler.END

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
            print("DEBUG: ENTER ANNOUNCE REGION command")
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
                announcementBubble = ""
                print(announcements)
                for announcement in announcements:
                    announcementBubble += f"Time: <Template date>\n"
                    announcementBubble += f"Neighbourhood: {str(announcement[0])}\n"
                    announcementBubble += f"Description: {str(announcement[1])}\n"
                    announcementBubble += f"Pax: {str(announcement[2])}\n"
    
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Initiatives in {selected_neighbourhood}:\n{announcementBubble}"
                )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Something went wrong. Please start over."
        )
    return ConversationHandler.END
#end helper

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
        print(f"DEBUG FULL ANNOUNCEMENT: {location}, {message}, {pax}")
        mycursor.execute("INSERT INTO Announcements (Location, Message, PAX) VALUES (%s, %s, %s)", (location, message, pax))
        mydb.commit()
       
  
        # fetch all the matching rows  
        mycursor.execute("SELECT * FROM Announcements") 
        ann = mycursor.fetchall() 
        
        # loop through the rows 
        print("Announcements Table:")
        for row in ann: 
            print(row)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Announcement has been made! 😊")
        
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You do not have permission to use this command.")
    return ConversationHandler.END
# end /announce

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
    
    join_handler = ConversationHandler(
        entry_points=[CommandHandler('join', join)],
        states={
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_type)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(join_handler)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
    