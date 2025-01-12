import asyncio
import requests
import websockets
import logging
import json
import Levenshtein
import sys
import time
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram_bot.telegram_utils import send_telegram_message_to_bot,send_telegram_message
from website.models import TrackingTokenNames, MemeCoins

# WebSocket URI
uri = "wss://pumpportal.fun/api/data"

# Define your bot's token
TELEGRAM_TOKEN = '7252788699:AAFjymiBcna1CZXYnpeB2EtVCJmeaXlxYUY'

group1_id = "-1002261635931"
group2_id = "-004607352219"

# Flag to manage WebSocket subscription state
is_connected = False
is_subscribed = False
websocket = None
count = 0
default_Multiplicity_value = 4
token_names = TrackingTokenNames.get_all_tokens()

# Set up logging to see what is happening
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Start command
async def start(update: Update, context: CallbackContext):
    print("User started the bot.")
    await update.message.reply_text(f'Welcome to the Token Bot! \n\nThese are the commands :\n\n/start\n/terminate\n/subscribe\n/unsubscribe\n/status\n/add_name\n/name_list\n/check_duplicate_count\n/set_duplicate_count')

# /subscribe command handler
async def subscribe(update: Update, context: CallbackContext):
    global is_subscribed, websocket, token_names, is_connected

    if len(token_names) == 0:
        send_telegram_message_to_bot("*Please add token names to the list before subscribing.*", parse_mode='Markdown')
        return

    if is_subscribed:
        send_telegram_message_to_bot("*Already subscribed to token creation events.*", parse_mode='Markdown')
        return

    async def subscribe_to_tokens():
        global websocket, is_subscribed, is_connected, uri, count
        try:
            if not websocket:
                async with websockets.connect(uri) as ws:
                    websocket = ws
                    print("Subscribing to new token creation events...")
                    logging.info("Subscribing to new token creation events...")
                    print("Running.....")

                    payload = {"method": "subscribeNewToken"}
                    await websocket.send(json.dumps(payload))

                    send_telegram_message_to_bot(f"*Successfully subscribed to new token creation events for token names:\n\n* {', '.join(token_names)}", parse_mode='Markdown')
                    is_subscribed = True

                    # Wait for incoming WebSocket messages
                    async for message in websocket:
                        data = json.loads(message)

                        token_symbol = data.get("symbol", "")
                        if token_symbol == "":
                            continue
                        #print(token_symbol)
                        token_name = data.get("name", "")
                        contract_address = data.get("mint", "")
                        developer = data.get("traderPublicKey", "")
                        url_link = data.get("uri", "")

                        # Call to add new token data
                        # If MemeCoins.add_meme_coin is async
                        asyncio.create_task(add_token_data_into_database (token_name, token_symbol,contract_address,developer,url_link))
                        # status= MemeCoins.add_meme_coin(token_name, token_symbol, contract_address, developer, url_link)

                        asyncio.create_task(check_same_token_availability(token_name, token_symbol,contract_address))

                        count += 1
                        if count % 100 == 0:
                            message = f"""⏰⏰⏰⏰⏰⏰\n\n *Token update - {count}*\n\n⏰⏰⏰⏰⏰⏰"""
                            send_telegram_message_to_bot(message, parse_mode='Markdown')
                            logging.info("Token update - {count}")
                            print(f"⏰⏰⏰⏰⏰⏰ Token update - {count} ⏰⏰⏰⏰⏰⏰")


                        asyncio.create_task(checking_tokens_from_token_list_and_send_telegram_message(token_name,token_symbol,contract_address,developer, url_link))
                        
                        # for name in token_names:
                        #     if name.lower() in token_name.lower() or name.lower() in token_symbol.lower():
                        #         match_percentage_token_name = get_match_percentage(name, token_name)
                        #         match_percentage_token_symbol = get_match_percentage(name, token_symbol)

                        #         data_array = get_ipfs_metadata(url_link)
                        #         image_url = data_array.get("image", "") if data_array else ""
                        #         twitter_url = data_array.get("twitter", "") if data_array else ""
                        #         website_url = data_array.get("website", "") if data_array else ""

                        #         empty_message = "\n⭕\n"
                        #         send_telegram_message_to_bot(empty_message, parse_mode='Markdown')

                        #         message = f"""
                        #         [🚨]({image_url}) *{name}* 🚨\n\n{token_name} ({token_symbol})\n\nName    - {match_percentage_token_name} %\nSymbol - {match_percentage_token_symbol} %\n\n📝 Contract Address: [🔍](https://solscan.io/token/{contract_address})\n{contract_address}\n\n📖 Deployer: [🔗](https://solscan.io/account/{developer})\n{developer}\n\nSolscan: [🔍](https://solscan.io/token/{contract_address})     PumpFun: [💊](https://pump.fun/coin/{contract_address})
                        #         \nTwitter: [🐦]({twitter_url})     Website: [🌐]({website_url})  
                        #         """
                        #         send_telegram_message_to_bot(message, parse_mode='Markdown')

        except Exception as e:
            send_telegram_message_to_bot(f"Error subscribing to WebSocket: {e}")
            logging.exception("Error subscribing to WebSocket: %s", str(e))
            print(f"Error subscribing to WebSocket: {e}")
            if websocket:
                await websocket.close()
                websocket = None
                is_connected = False
            is_connected = False
        finally:
            if is_subscribed:
                send_telegram_message_to_bot("*WebSocket task completed or failed (Still Subscribed TRUE).*", parse_mode='Markdown')
                print("WebSocket task completed or failed (Still Subscribed TRUE).")
                logging.info("WebSocket task completed or failed (Still Subscribed TRUE).")


                asyncio.create_task(subscribe_to_tokens())

                send_telegram_message_to_bot("*started again (Subscribed automatically).*", parse_mode='Markdown')
                is_connected = True
            else:
                send_telegram_message_to_bot("*WebSocket task completed or failed.*", parse_mode='Markdown')
                print("WebSocket task completed or failed.")
                logging.info("WebSocket task completed or failed.")

                send_telegram_message_to_bot("*Successfully unsubscribed from new token creation events.*", parse_mode='Markdown')
                is_connected = False
                is_subscribed = False

    asyncio.create_task(subscribe_to_tokens())
    is_subscribed = True

# /unsubscribe command
async def unsubscribe(update: Update, context: CallbackContext):
    global is_subscribed, websocket, is_connected
    try:
        if websocket:
            payload = {"method": "unsubscribeNewToken"}
            await websocket.send(json.dumps(payload))
            send_telegram_message_to_bot("*Successfully unsubscribed from new token creation events.*", parse_mode='Markdown')
            print("Successfully unsubscribed from new token creation events.")
            logging.info("Successfully unsubscribed from new token creation events.")

        else:
            send_telegram_message_to_bot("*Already Unsubscribed.*", parse_mode='Markdown')
            print("Already Unsubscribed.")
    except Exception as e:
        send_telegram_message_to_bot(f"An error occurred while unsubscribing: {e}", parse_mode='Markdown')
        print(f"An error occurred while unsubscribing: {e}")
        logging.exception("An error occurred while unsubscribing: %s", str(e))

    finally:
        if websocket:
            await websocket.close()
        websocket = None
        is_connected = False
        is_subscribed = False

# /status command
async def status(update: Update, context: CallbackContext):
    if is_subscribed:
        send_telegram_message_to_bot(f"*You are currently subscribed to new token events for token names:* {', '.join(token_names)}", parse_mode='Markdown')
    else:
        send_telegram_message_to_bot("*You are not subscribed to any token events.*", parse_mode='Markdown')

# /add_name command
async def add_name(update: Update, context: CallbackContext):
    global token_names
    if len(context.args) == 0:
        send_telegram_message_to_bot("*Please provide a token name to add to the list as* `/add_name` name.", parse_mode='Markdown')
        return

    token_name = context.args[0]
    
    if token_name in token_names:
        send_telegram_message_to_bot(f"The token name '{token_name}' is already in the list.")
        return
    add_status = TrackingTokenNames.add_token(token_name)
    if add_status:
        send_telegram_message_to_bot(f"Token name '{token_name}' added to the list.")
        token_names = TrackingTokenNames.get_all_tokens()
    else:
        send_telegram_message_to_bot(f"Error - Adding Token name '{token_name}' in to the list.")

# List token names and allow deletion
async def name_list(update: Update, context: CallbackContext):
    token_names = TrackingTokenNames.get_all_tokens()

    if len(token_names) == 0:
        send_telegram_message_to_bot("The list of token names is currently empty.")
        return

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"delete_{name}") for name in token_names]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Here is the list of token names. Click on a token to delete it:", reply_markup=reply_markup)

# Handle delete button press
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    token_name = query.data.split('_')[1] 

    # Ask for confirmation to delete the token name
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data=f"yes_{token_name}")],
        [InlineKeyboardButton("No", callback_data=f"no_{token_name}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Do you want to DELETE the token name '{token_name}'?", reply_markup=reply_markup)

# Delete token after confirmation
async def delete_token(update: Update, context: CallbackContext):
    query = update.callback_query
    action, token_name = query.data.split('_')

    if action == 'yes':
        if token_name in token_names:
            del_status = TrackingTokenNames.delete_token(token_name)
            if del_status:
                await query.edit_message_text(f"Token name '{token_name}' has been deleted.")
                token_names.remove(token_name)
            else:
                await query.edit_message_text(f"Error - Token name '{token_name}' not deleted.")
        else:
            await query.edit_message_text(f"Token name '{token_name}' was not found in the list.")
    else:
        await query.edit_message_text(f"Token name '{token_name}' was not deleted.")

# /status command
async def check_duplicate_count(update: Update, context: CallbackContext):
    global default_Multiplicity_value
    send_telegram_message_to_bot(f"*Duplicate count set as {default_Multiplicity_value}*", parse_mode='Markdown')
    

# /set duplicate count command
async def set_duplicate_count(update: Update, context: CallbackContext):
    global default_Multiplicity_value
 
    if len(context.args) == 0:
        send_telegram_message_to_bot("*Please provide a number as this* `/set_duplicate_count` number.", parse_mode='Markdown')
        return

    entered_value = context.args[0]

    # Check if entered value is a valid number
    if not entered_value.isdigit():  # Checks if it's a whole number (non-negative)
        send_telegram_message_to_bot(f"'{entered_value}' is not a valid number. Please provide a valid number with the comand.", parse_mode='Markdown')
        return

    # If it's a number, set the duplicate_count
    default_Multiplicity_value = int(entered_value)
    send_telegram_message_to_bot(f"Duplicate count has been set to {default_Multiplicity_value}.", parse_mode='Markdown')

# /status command
terminate_status = False
async def terminate_the_programme(update: Update, context: CallbackContext):
    global terminate_status
    
    if len(context.args) == 0:
        send_telegram_message_to_bot("*Are you sure to terminate the copy this and message* `/terminate yes`.", parse_mode='Markdown')
        return

    terminate = context.args[0]
    
    print(terminate_status)
    if terminate_status:
        if terminate == "yes" and terminate_status:
            terminate = "no"
            # Some code...
            message= "Terminate the program within 5 second (stopped running code)"
            send_telegram_message_to_bot(message, parse_mode='Markdown')
            send_telegram_message(message,group1_id, parse_mode='Markdown')

            time.sleep(5)
            print("Terminated the proggrame")
            logging.info("Terminated the proggrame")
            #Exit the script
            sys.exit()

            message= "Error - Terminate unsuccessfull\nPrograme is still running"
            send_telegram_message_to_bot(message, parse_mode='Markdown')
            send_telegram_message(message,group1_id, parse_mode='Markdown')
            print("Error - Terminate unsuccessfull. Programe is still running")
            logging.info("Error - Terminate unsuccessfull. Programe is still running")

        else:
            send_telegram_message_to_bot(f"invalid input. copy and send this command `/terminate yes`")
            
    terminate_status = True



# Main function to set up the Telegram bot
async def run_telegram_bot():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("add_name", add_name))
    application.add_handler(CommandHandler("name_list", name_list))
    application.add_handler(CommandHandler("check_duplicate_count", check_duplicate_count))
    application.add_handler(CommandHandler("set_duplicate_count", set_duplicate_count))
    application.add_handler(CommandHandler("terminate", terminate_the_programme))

    # Register callback handlers
    application.add_handler(CallbackQueryHandler(button, pattern="^delete_"))
    application.add_handler(CallbackQueryHandler(delete_token, pattern="^yes_|^no_"))

    print("Starting bot...")
    logging.info("Starting bot...")

    await application.run_polling()
    print("Bot is now running.")
    logging.info("Bot is now running.")


    #commands in telgram

        # /start
        # /subscribe
        # /unsubscribe
        # /status
        # /add_name
        # /name_list
        # /check_duplicate_count
        # /set_duplicate_count
        # /get_chat_ids
        # /terminate




# Additional functions

MAX_CONCURRENT_TASKS = 5  
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

async def check_same_token_availability(token_name, token_symbol,contract_address):
    global default_Multiplicity_value, group1_id

    try:
        async with semaphore:
            availability = MemeCoins.check_token_availability(token_name, token_symbol,default_Multiplicity_value)

            if availability[0]:
                if availability[2]:
                    tokens_list = MemeCoins.get_tokens_by_ticker(availability[1])
                    # message = f"""😍😍\n\n *New Token Found From TICKER* 😍😍\n\n `{availability[1]}`\n\n *coins count - {len(tokens_list)}*\n\n"""
                    # send_telegram_message(message,group1_id, parse_mode='Markdown')
                else:
                    tokens_list = MemeCoins.get_tokens_by_name(availability[1])
                    # message = f"""😍😍\n\n *New Token Found in NAME- {availability[1]}*\n\n coins count - {len(tokens_list)}\n\n😍😍"""
                    # send_telegram_message(message,group1_id, parse_mode='Markdown')

                #to get developer have only one tokeb in this name
                unique_tokens = get_unique_tokens(tokens_list)
                total_tokens_count = len(tokens_list)

                send_telegram_message_if_found_a_trending_token(unique_tokens,total_tokens_count,token_symbol,token_name,contract_address, group1_id)
    
    except Exception as e:
        logging.error(f"Error checking token availability: {e}")

            
async def add_token_data_into_database(token_name, token_symbol, contract_address, developer, url_link):
    try:
        async with semaphore:

            data = get_ipfs_metadata(url_link)
            twitter_link = data.get("twitter", "no") if data else "no"

            status = MemeCoins.add_meme_coin(token_name, token_symbol, contract_address, developer, url_link,twitter_link)
            if not status:
                logging.warning(f"Failed to add token {token_name} to the database.")

            if twitter_link != "no":
                asyncio.create_task(send_telegram_message_if_same_twitter_connected(twitter_link,token_symbol,token_name,contract_address))


    except Exception as e:
        logging.error(f"Error adding token data to database: {e}")


async def send_telegram_message_if_same_twitter_connected(twitter_link,token_symbol,token_name,contract_address):
    global group2_id
    try:
        async with semaphore:
            tokens_list=MemeCoins.get_tokens_by_twitter_link(twitter_link)
            total_tokens_count=len(tokens_list)
            if total_tokens_count > 0 :
                unique_tokens_list=get_unique_tokens(tokens_list)
                send_telegram_message_if_found_a_trending_token(unique_tokens_list,total_tokens_count,token_symbol,token_name,contract_address,group2_id)
                
    except Exception as e:
        logging.error(f"Error adding token data to database: {e}")
 

async def checking_tokens_from_token_list_and_send_telegram_message (token_name,token_symbol,contract_address,developer,url_link):
    global token_names

    try:
        async with semaphore:
            for name in token_names:
                if name.lower() in token_name.lower() or name.lower() in token_symbol.lower():
                    match_percentage_token_name = get_match_percentage(name, token_name)
                    match_percentage_token_symbol = get_match_percentage(name, token_symbol)

                    data_array = get_ipfs_metadata(url_link)
                    image_url = data_array.get("image", "") if data_array else ""
                    twitter_url = data_array.get("twitter", "") if data_array else ""
                    website_url = data_array.get("website", "") if data_array else ""

                    empty_message = "\n⭕\n"
                    send_telegram_message_to_bot(empty_message, parse_mode='Markdown')

                    message = f"""
                    [🚨]({image_url}) *{name}* 🚨\n\n`{token_name}` (`{token_symbol}`)\n\nName    - {match_percentage_token_name} %\nSymbol - {match_percentage_token_symbol} %\n\n📝 Contract Address: [🔍](https://solscan.io/token/{contract_address})\n`{contract_address}`\n\n🙋‍♂️ Deployer: [🔗](https://solscan.io/account/{developer})\n{developer}\n\nSolscan: [🔍](https://solscan.io/token/{contract_address})     PumpFun: [💊](https://pump.fun/coin/{contract_address})
                    \nTwitter: [🐦]({twitter_url})     Website: [🌐]({website_url})  
                    """
                    send_telegram_message_to_bot(message, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Error checking tokens and sending message: {e}")



def get_ipfs_metadata(ipfs_url):
    try:
        response = requests.get(ipfs_url)
        if response.status_code == 200:
            return response.json()
        else:
            
            print(f"Failed to retrieve metadata. Status code: {response.status_code}")
            logging.info(f"Failed to retrieve metadata. Status code: {response.status_code}")
            logging.info(f"ipfs URL: {ipfs_url}")

            print (ipfs_url)
            return None
        
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        logging.exception("An error occurred: %s", str(e))
        return None

def get_match_percentage(str1, str2):
    distance = Levenshtein.distance(str1.lower(), str2.lower())
    max_len = max(len(str1), len(str2))
    if max_len == 0:
        return 100
    match_percentage = (1 - distance / max_len) * 100
    return int(match_percentage)


def get_unique_tokens(tokens_list):
    # Extract all dev_address values
    dev_addresses = [token["dev_address"] for token in tokens_list]

    # Count occurrences of each dev_address using Counter
    dev_address_counts = Counter(dev_addresses)

    # Filter out dev_addresses that appear only once
    unique_dev_addresses = [dev_address for dev_address, count in dev_address_counts.items() if count == 1]

    # Get tokens that have these unique dev_addresses
    unique_tokens = [token for token in tokens_list if token["dev_address"] in unique_dev_addresses]

    return unique_tokens




# def send_telegram_message_to_group2(unique_tokens,total_tokens_count,token_symbol,token_name,contract_address):
#     global default_Multiplicity_value ,group2_id
    
#     new_image_url = f"https://pump.fun/coin/{contract_address}"
#     genuine_or_not = "❌"
    
#     unique_tokens_count = len(unique_tokens)
#     if not len (unique_tokens)==0:
#         genuine_list_string =f"⤵️⤵️ *Genuine  List ({unique_tokens_count}/{total_tokens_count})* ⤵️⤵️"
#         i=0
#         for token in unique_tokens :
#             #  token = {
#             #         "token_name": token.token_name, 
#             #         "token_ticker": token.token_ticker,
#             #         "contract_address": token.contract_adddress,
#             #         "dev_address": token.dev_address,
#             #         "metadata_link": token.metadata_link
#             #         }
#             g_token_name = escape_markdown(token.get("token_name"))
#             g_token_ticker = escape_markdown(token.get("token_ticker"))
#             g_contract_address = token.get("contract_address")
#             g_dev_address = token.get("dev_address")
#             g_metadata_link = token.get("metadata_link")

#             i=i+1
#             meta_data = get_ipfs_metadata(g_metadata_link)
#             if i==1:
#                 image_link = meta_data.get("image", None) if meta_data else None
#                 if image_link:
#                     new_image_url= image_link

#                 if g_contract_address == contract_address :
#                     genuine_or_not = "✅"

#             # Using escape_markdown with None values now handled properly
#             website_url = meta_data.get("website", None) if meta_data else None
#             telegram_url = meta_data.get("telegram", None) if meta_data else None
#             twitter_url = meta_data.get("twitter", None) if meta_data else None

#             website_url_string =""
#             telegram_url_string =""
#             twitter_url_string=""
#             twitter_user_name_string=""
#             if website_url :
#                 website_url_string = f" [🌐]({website_url})" 

#             if telegram_url :
#                 telegram_url_string = f" [📱]({telegram_url})" 

#             if twitter_url :
#                 twitter_url_string = f" [🐦]({twitter_url})"
#                 twitter_user_name_string= f" - @{escape_markdown(twitter_url.split('/')[-1])}"


#             genuine_list_string = genuine_list_string + f"""\n\n*{f"{i:02d}" if i < 10 else str(i)}*. `{g_token_name}`(`{g_token_ticker}`)\n  [💊](https://pump.fun/coin/{g_contract_address}) [📝](https://solscan.io/token/{g_contract_address}) [🙋‍♂️](https://solscan.io/account/{g_dev_address}){website_url_string}{telegram_url_string}{twitter_url_string}{twitter_user_name_string} """
                  
#     else:
#         genuine_list_string ="⤵️⤵️ *GENUINE LIST* ⤵️⤵️\n\n   No Genuine Tokens ❌"
    

#     if total_tokens_count == default_Multiplicity_value:
#         topic =f"[😍]({new_image_url}) *New Trending Token Found* 😍"
#     else:
#         topic = f"[🔥]({new_image_url}) *New Update* 🔥"

#     main_message = f"""

#     {topic}\n\n`{escape_markdown(token_name)}` (`{escape_markdown(token_symbol)}`) {genuine_or_not}\n\nMultiplicity : *{total_tokens_count}*  (default {default_Multiplicity_value})\n\n✔️ *{unique_tokens_count} Genuine* | ❌  *{total_tokens_count - unique_tokens_count } Fake*\n\n{genuine_list_string}\n\n..."""

#     empty_message = "\n⭕\n"
#     send_telegram_message(empty_message, group2_id,parse_mode='Markdown')

#     send_telegram_message(main_message,group2_id, parse_mode='Markdown')


    
def send_telegram_message_if_found_a_trending_token(unique_tokens,total_tokens_count,token_symbol,token_name,contract_address,groupId):
    global default_Multiplicity_value 
    
    new_image_url = f"https://pump.fun/coin/{contract_address}"
    genuine_or_not = "❌"
    
    unique_tokens_count = len(unique_tokens)
    if not len (unique_tokens)==0:
        genuine_list_string =f"⤵️⤵️ *Genuine  List ({unique_tokens_count}/{total_tokens_count})* ⤵️⤵️"
        i=0
        for token in unique_tokens :
            #  token = {
            #         "token_name": token.token_name, 
            #         "token_ticker": token.token_ticker,
            #         "contract_address": token.contract_adddress,
            #         "dev_address": token.dev_address,
            #         "metadata_link": token.metadata_link
            #         }
            g_token_name = escape_markdown(token.get("token_name"))
            g_token_ticker = escape_markdown(token.get("token_ticker"))
            g_contract_address = token.get("contract_address")
            g_dev_address = token.get("dev_address")
            g_metadata_link = token.get("metadata_link")

            i=i+1
            meta_data = get_ipfs_metadata(g_metadata_link)
            if i==1:
                image_link = meta_data.get("image", None) if meta_data else None
                if image_link:
                    new_image_url= image_link

                if g_contract_address == contract_address :
                    genuine_or_not = "✅"

            # Using escape_markdown with None values now handled properly
            website_url = meta_data.get("website", None) if meta_data else None
            telegram_url = meta_data.get("telegram", None) if meta_data else None
            twitter_url = meta_data.get("twitter", None) if meta_data else None

            website_url_string =""
            telegram_url_string =""
            twitter_url_string=""
            twitter_user_name_string=""
            if website_url :
                website_url_string = f" [🌐]({website_url})" 

            if telegram_url :
                telegram_url_string = f" [📱]({telegram_url})" 

            if twitter_url :
                twitter_url_string = f" [🐦]({twitter_url})"
                twitter_user_name_string= f" - @{escape_markdown(twitter_url.split('/')[-1])}"


            genuine_list_string = genuine_list_string + f"""\n\n*{f"{i:02d}" if i < 10 else str(i)}*. `{g_token_name}`(`{g_token_ticker}`)\n  [💊](https://pump.fun/coin/{g_contract_address}) [📝](https://solscan.io/token/{g_contract_address}) [🙋‍♂️](https://solscan.io/account/{g_dev_address}){website_url_string}{telegram_url_string}{twitter_url_string}{twitter_user_name_string} """
                  
    else:
        genuine_list_string ="⤵️⤵️ *GENUINE LIST* ⤵️⤵️\n\n   No Genuine Tokens ❌"
    

    if total_tokens_count == default_Multiplicity_value:
        topic =f"[😍]({new_image_url}) *New Trending Token Found* 😍"
    else:
        topic = f"[🔥]({new_image_url}) *New Update* 🔥"

    main_message = f"""

    {topic}\n\n`{escape_markdown(token_name)}` (`{escape_markdown(token_symbol)}`) {genuine_or_not}\n\nMultiplicity : *{total_tokens_count}*  (default {default_Multiplicity_value})\n\n✔️ *{unique_tokens_count} Genuine* | ❌  *{total_tokens_count - unique_tokens_count } Fake*\n\n{genuine_list_string}\n\n..."""

    empty_message = "\n⭕\n"
    send_telegram_message(empty_message, groupId,parse_mode='Markdown')

    send_telegram_message(main_message,groupId, parse_mode='Markdown')


def escape_markdown(text):
    # Check if the input is None, and if so, replace it with an empty string
    if text is None:
        return ''
    
    # List of special markdown characters to escape
    markdown_chars = ['*', '_', '~', '`', '[', ']', '(', ')', '#', '+', '-', '!', '|', '<', '>', '=', '.', ':']
    
    # Iterate through each markdown character and escape it
    for char in markdown_chars:
        text = text.replace(char, f"\\{char}")
    
    return text






