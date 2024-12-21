import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters,ConversationHandler
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

mydb=mysql.connector.connect(
    host="localhost",
    user='root',
    password = os.getenv('MYSQL_PASS'),
)

mycursor = mydb.cursor()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
TOKEN = os.getenv('TOKEN')
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="hi")
    
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = (
        "Here is a list of commands you can use:\n\n"
        "/help - Displays this help message.\n"
        "/join <BUSINESS/INDIVIDUAL NAME> - Assign business/ Individual name\n"
        "/nearby - List announcements for areas near you. Run /nearby without locations for a list of available locations\n"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_message )
    

# Define states
REGION, NEIGHBOURHOOD = range(2)

async def nearby_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    regions_info = """
    = NORTH =
    Sembawang
    Woodlands
    Yishun

    = NORTH-EAST =
    Ang Mo Kio
    Hougang
    Punggol
    Sengkang
    Serangoon

    = EAST =
    Bedok
    Pasir Ris
    Tampines

    = WEST =
    Bukit Batok
    Bukit Panjang
    Choa Chu Kang
    Clementi
    Jurong East
    Jurong West
    Tengah

    = CENTRAL =
    Bishan
    Bukit Merah
    Bukit Timah
    Central Area
    Geylang
    Kallang/Whampoa
    Marine Parade
    Queenstown
    Toa Payoh
    """
    await context.bot.send_message(chat_id=update.effective_chat.id, text=regions_info)

    region_buttons = [["North", "North-East"], ["East", "West"], ["Central"]]
    reply_markup = ReplyKeyboardMarkup(region_buttons, one_time_keyboard=True, resize_keyboard=True)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please select a general region to proceed:",
        reply_markup=reply_markup
    )
    return REGION

regions = {
    "North": ["Sembawang", "Woodlands", "Yishun"],
    "North-East": ["Ang Mo Kio", "Hougang", "Punggol", "Sengkang", "Serangoon"],
    "East": ["Bedok", "Pasir Ris", "Tampines"],
    "West": ["Bukit Batok", "Bukit Panjang", "Choa Chu Kang", "Clementi", "Jurong East", "Jurong West", "Tengah"],
    "Central": ["Bishan", "Bukit Merah", "Bukit Timah", "Central Area", "Geylang", "Kallang/Whampoa", "Marine Parade", "Queenstown", "Toa Payoh"]
}
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
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"You have selected {selected_neighbourhood} in the {selected_region} region."
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Something went wrong. Please start over."
        )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Operation canceled."
    )
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Add ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("nearby", nearby_command)],
        states={
            REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, region_selected)],
            NEIGHBOURHOOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, neighbourhood_selected)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)
    

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()