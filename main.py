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
USER = os.getenv('USER')

# mydb = mysql.connector.connect(
#     host="localhost",
#     user= USER,
#     password = PASS,
#     database = "sustainibbles"
# )

# mycursor = mydb.cursor()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# cursor = mydb.cursor()

TOKEN = os.getenv('TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Formatting styles for Markdown V2
    start_bold = "\033[1m"
    end_bold = "\033[0m"
    underline = "\033[4m"

    # Terms and Conditions message
    terms = f"""
{start_bold}Welcome to Sustainibbles!{end_bold}

By using this bot, you agree to the following terms and conditions. Please read them carefully before proceeding.

---

1. {start_bold}Purpose{end_bold}  
This bot facilitates the sharing of surplus food from businesses to individuals in need, promoting sustainability and reducing food waste.

---

2. {start_bold}Eligibility{end_bold}  
{start_bold}Individuals{end_bold}: You must be at least 18 years old to use this bot.  
{start_bold}Businesses{end_bold}: Only verified businesses may register to share surplus food.

---

3. {start_bold}Responsibility of Users{end_bold}  
{underline}Businesses{end_bold}:  
  Ensure that surplus food shared is safe and consumable at the time of notification.  
  Provide accurate details about the food, including quantity, type, and pickup time/location.  
{underline}Individuals{end_bold}:  
  Collect food within the specified timeframe and location provided by businesses.  
  Confirm you understand and accept the condition of the food.

---

4. {start_bold}Food Safety and Liability{end_bold}  
This bot does not verify the quality, safety, or condition of the food being shared.  
The bot and its creators are not responsible for any adverse effects arising from the consumption of food obtained through this service.  
Food recipients consume the food at their own risk.

---

5. {start_bold}Prohibited Use{end_bold}  
Misuse of the bot, including providing false information, harassment, or any illegal activity, is strictly prohibited.  
Businesses must not share expired or hazardous food.

---

6. {start_bold}Data Privacy{end_bold}  
The bot collects and uses minimal data required for notifications and interactions.  
We do not share your personal information with third parties without your consent.

---

7. {start_bold}Modifications to Terms{end_bold}  
These terms may be updated periodically. Users will be notified of significant changes, and continued use of the bot constitutes acceptance of the updated terms.

---

8. {start_bold}Disclaimer of Warranties{end_bold}  
This service is provided “as is” without any warranties, express or implied.  
We do not guarantee uninterrupted or error-free operation of the bot.

---

9. {start_bold}Termination of Access{end_bold}  
We reserve the right to suspend or terminate access to the bot for any user who violates these terms.

---

10. {start_bold}Governing Law{end_bold}  
These terms and conditions are governed by the laws of [Jurisdiction], without regard to its conflict of law provisions.

---

{underline}By using this bot, you confirm that you have read, understood, and agree to these terms and conditions.{end_bold}
"""

    # Send the message
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=terms
    )

# async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """BUSINESS: Announce details of food surplus\nFormat:\nLOCATION: <location>\nMESSAGE: <message>\nPAX: <pax>"""
#     message = update.message.text
#     user_id = update.effective_user.id
    
#     cursor.execute("SELECT * FROM users where username == %s", user_id)
#     result = cursor.fetchone()

#     if result and result['role'] == "business":
#         location = message.split("LOCATION: ")[1].split("\n")[0]
#         message = message.split("MESSAGE: ")[1].split("\n")[0]
#         pax = message.split("PAX: ")[1].split("\n")[0]
        
#         cursor.execute("INSERT INTO announcements (location, message, pax) VALUES (%s, %s, %s)", (location, message, pax))
        
#         await context.bot.send_message(chat_id=update.effective_chat.id, text="Announcement has been made!")
#     else:
#         await context.bot.send_message(chat_id=update.effective_chat.id, text="You do not have permission to use this command.")

NAME, TYPE = range(2)

# /join function
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Automatically set the user's name as their effective_user.id
    context.user_data["name"] = update.effective_user.id
    type_buttons = [["Individual"], ["Business"]]
    reply_markup = ReplyKeyboardMarkup(type_buttons, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        text="Welcome! Your user ID has been set as your name. Please select a type:",
        reply_markup=reply_markup
    )
    return TYPE

async def set_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Retrieve the name and selected type
    name = str(context.user_data.get("name"))
    type_ = update.message.text

    # Validate the type selection
    if type_ not in ["Individual", "Business"]:
        await update.message.reply_text("Invalid selection. Please choose either 'Individual' or 'Business' using the buttons.")
        return TYPE  # Stay in the TYPE state

    # Check if the user already exists in the database
    try:
        cursor.execute("SELECT * FROM Users WHERE Name = %s", (name,))
        result = cursor.fetchone()

        if result:
            await update.message.reply_text(f"Record already exists for ID: {name}.")
        else:
            # Insert the new record if it doesn't exist
            cursor.execute("INSERT INTO Users (Name, Type) VALUES (%s, %s)", (name, type_))
            mydb.commit()
            await update.message.reply_text(f"Successfully registered ID: {name} with type: {type_}!")
    except mysql.connector.Error as err:
        await update.message.reply_text(f"Database error: {err}")
        print(f"Database error: {err}")

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
    # application.add_handler(CommandHandler("announce", announce))

    # on non command i.e message - echo the message on Telegram
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Add conversation handler for /join
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("join", join)],
        states={
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_type)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()