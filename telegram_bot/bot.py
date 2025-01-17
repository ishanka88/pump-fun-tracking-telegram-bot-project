import asyncio
import websockets
import logging
import json
import sys
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext,MessageHandler, MessageHandler, filters,Updater
from telegram_bot.telegram_utils import send_telegram_message_to_admin,send_telegram_message_to_users,delete_message
from website.models import TrackingTokenNames,FakeTwitterAccounts,MessageIdBasedOnTwitter,MemeCoins
from telegram_bot  import methods
from config import Config


# Flag to manage WebSocket subscription state
is_connected = False
is_subscribed = False
websocket = None
count = 0
Config.TOKEN_NAMES_LIST = TrackingTokenNames.get_all_tokens()
Config.FAKE_TWITTER_LIST = FakeTwitterAccounts.get_all_accounts()


# Start command
async def start(update: Update, context: CallbackContext):
    print("User started the bot.")
    user_id = str(update.message.from_user.id)
    group_id = str(update.message.chat.id)
    
    if user_id == Config.ADMIN_ID and group_id==Config.ADMIN_ID:
        await update.message.reply_text(f'Welcome to the Token Bot! \n\nThese are the commands :\n\n/start\n/terminate\n/subscribe\n/unsubscribe\n/status\n/add_name\n/name_list\n/check_duplicate_count\n/set_duplicate_count\n/check_genuine_display_count\n/set_genuine_display_count')
    else:
        
        await update.message.reply_text(f'Welcome to the Token Bot! \n\nThese are the commands :\n\n/start\n/status\n/check_duplicate_count\n/check_genuine_display_count')

# /subscribe command handler
async def subscribe(update: Update, context: CallbackContext):
    global is_subscribed, websocket, is_connected
    user_id = str(update.message.from_user.id)
    group_id = str(update.message.chat.id)

    if user_id == Config.ADMIN_ID and group_id==Config.ADMIN_ID:
        if len(Config.TOKEN_NAMES_LIST) == 0:
            send_telegram_message_to_admin("*Please add token names to the list before subscribing.*", parse_mode='Markdown')
            return

        if is_subscribed:
            send_telegram_message_to_admin("*Already subscribed to token creation events.*", parse_mode='Markdown')
            return

        async def subscribe_to_tokens():
            global websocket, is_subscribed, is_connected, count
            try:
                if not websocket:
                    async with websockets.connect(Config.WEBSOCKET_URI) as ws:
                        websocket = ws
                        print("Subscribing to new token creation events...")
                        logging.info("Subscribing to new token creation events...")
                        print("Running.....")

                        payload = {"method": "subscribeNewToken"}
                        await websocket.send(json.dumps(payload))

                        send_telegram_message_to_admin(f"*Successfully subscribed to new token creation events for token names:\n\n* {', '.join(Config.TOKEN_NAMES_LIST)}", parse_mode='Markdown')
                        is_subscribed = True

                        # Wait for incoming WebSocket messages
                        async for message in websocket:
                            data = json.loads(message)

                            token_ticker = data.get("symbol", "")
                            if token_ticker == "":
                                continue
                            #rint(token_ticker)

                            token_name = data.get("name", "")
                            contract_address = data.get("mint", "")
                            dev_address = data.get("traderPublicKey", "")
                            metadata_link = data.get("uri", "")
                            initial_buy = data.get("initialBuy", 0.0)
                            sol_amount = data.get("solAmount", 0.0)
                            bonding_curve_key = data.get("bondingCurveKey", "")
                            v_tokens_in_bonding_curve = data.get("vTokensInBondingCurve", 0.0)
                            v_sol_in_bonding_curve = data.get("vSolInBondingCurve", 0.0)
                            market_cap_sol = data.get("marketCapSol", 0.0)
                            signature = data.get("signature", "")

                            # add memecoin in to data base
                            asyncio.create_task(methods.add_token_data_into_database (token_name, token_ticker, contract_address, dev_address, metadata_link
                                        ,initial_buy, sol_amount, bonding_curve_key, v_tokens_in_bonding_curve
                                            ,v_sol_in_bonding_curve, market_cap_sol, signature))
                            
                            # Check same token availability from name and symbol
                            asyncio.create_task(methods.check_same_token_availability_in_database(token_name, token_ticker,contract_address))

                            #check token vailable in the checking list and if available send a telegram message 
                            asyncio.create_task(methods.check_token_name_available_in_the_list_and_send_telegram_message(token_name,token_ticker,contract_address,dev_address, metadata_link))

                            count += 1
                            if count % 100 == 0:
                                message = f"""⏰⏰⏰⏰⏰⏰\n\n *Token update - {count}*\n\n⏰⏰⏰⏰⏰⏰"""
                                send_telegram_message_to_admin(message, parse_mode='Markdown')
                                logging.info("Token update - {count}")
                                print(f"⏰⏰⏰⏰⏰⏰ Token update - {count} ⏰⏰⏰⏰⏰⏰")


                            
            except Exception as e:
                send_telegram_message_to_admin(f"Error subscribing to WebSocket: {e}")
                logging.exception("Error subscribing to WebSocket: %s", str(e))
                print(f"Error subscribing to WebSocket: {e}")
                if websocket:
                    await websocket.close()
                    websocket = None
                    is_connected = False
                is_connected = False
            finally:
                if is_subscribed:
                    send_telegram_message_to_admin("*WebSocket task completed or failed (Still Subscribed TRUE).*", parse_mode='Markdown')
                    print("WebSocket task completed or failed (Still Subscribed TRUE).")
                    logging.info("WebSocket task completed or failed (Still Subscribed TRUE).")


                    asyncio.create_task(subscribe_to_tokens())

                    send_telegram_message_to_admin("*started again (Subscribed automatically).*", parse_mode='Markdown')
                    is_connected = True
                else:
                    send_telegram_message_to_admin("*WebSocket task completed or failed.*", parse_mode='Markdown')
                    print("WebSocket task completed or failed.")
                    logging.info("WebSocket task completed or failed.")

                    send_telegram_message_to_admin("*Successfully unsubscribed from new token creation events.*", parse_mode='Markdown')
                    is_connected = False
                    is_subscribed = False

        asyncio.create_task(subscribe_to_tokens())
        is_subscribed = True

# /unsubscribe command
async def unsubscribe(update: Update, context: CallbackContext):
    global is_subscribed, websocket, is_connected
    try:
        user_id = str(update.message.from_user.id)
        group_id = str(update.message.chat.id)

        if user_id == Config.ADMIN_ID and group_id==Config.ADMIN_ID:
            if websocket:
                payload = {"method": "unsubscribeNewToken"}
                await websocket.send(json.dumps(payload))
                send_telegram_message_to_admin("*Successfully unsubscribed from new token creation events.*", parse_mode='Markdown')
                print("Successfully unsubscribed from new token creation events.")
                logging.info("Successfully unsubscribed from new token creation events.")

            else:
                send_telegram_message_to_admin("*Already Unsubscribed.*", parse_mode='Markdown')
                print("Already Unsubscribed.")
    except Exception as e:
        send_telegram_message_to_admin(f"An error occurred while unsubscribing: {e}", parse_mode='Markdown')
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
        await update.message.reply_text(f"*You are currently subscribed to new token events for token names:* {', '.join(Config.TOKEN_NAMES_LIST)}", parse_mode='Markdown')
    else:
        await update.message.reply_text("*You are not subscribed to any token events.*", parse_mode='Markdown')

# /add_name command
async def add_name(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    group_id = str(update.message.chat.id)

    if user_id == Config.ADMIN_ID and group_id==Config.ADMIN_ID:  
        if len(context.args) == 0:
            send_telegram_message_to_admin("*Please provide a token name to add to the list as* `/add_name` name.", parse_mode='Markdown')
            return

        token_name = " ".join(context.args)
        
        if token_name in Config.TOKEN_NAMES_LIST:
            send_telegram_message_to_admin(f"The token name '{token_name}' is already in the list.")
            return
        add_status = TrackingTokenNames.add_token(token_name)
        if add_status:
            send_telegram_message_to_admin(f"Token name '{token_name}' added to the list.")
            Config.TOKEN_NAMES_LIST = TrackingTokenNames.get_all_tokens()
        else:
            send_telegram_message_to_admin(f"Error - Adding Token name '{token_name}' in to the list.")


# Delete token after confirmation
async def delete_token(update: Update, context: CallbackContext):
    try:
        query = update.callback_query
        user_id = str(query.from_user.id)  # User ID from the callback query
        group_id = str(query.message.chat.id ) # Chat ID from the message

        if user_id == Config.ADMIN_ID and group_id==Config.ADMIN_ID:
            query = update.callback_query
            parts = query.data.split('_',1) # Split at the first underscore only
            action = parts[0]
            token_name=parts[1]

            if action == 'yesDelete':
                
                if token_name in Config.TOKEN_NAMES_LIST:
                    del_status = TrackingTokenNames.delete_token(token_name)
                    if del_status:
                        await query.edit_message_text(f"Token name '{token_name}' has been deleted.")
                        Config.TOKEN_NAMES_LIST.remove(token_name)
                    else:
                        await query.edit_message_text(f"Error - Token name '{token_name}' not deleted.")
                else:
                    await query.edit_message_text(f"Token name '{token_name}' was not found in the list.")
            elif action=='noDelete':
                await query.edit_message_text(f"Token name '{token_name}' was not Delete.")
    except Exception as e:
        logging.exception(f"Error : delete Token {e}")
        print(f"Error : delete Token {e}")

# List token names and allow deletion
async def check_name_list(update: Update, context: CallbackContext):
    try:
        user_id = str(update.message.from_user.id)
        group_id = str(update.message.chat.id)

        if user_id == Config.ADMIN_ID and group_id==Config.ADMIN_ID:
            token_names = TrackingTokenNames.get_all_tokens()
            if len(token_names) == 0:
                await update.message.reply_text("The list of token names is currently empty.")
                return

            keyboard = [
                [InlineKeyboardButton(name, callback_data=f"delete_{name}") for name in token_names]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Here is the list of token names. Click on a token to delete it:", reply_markup=reply_markup)
    except Exception as e:
        logging.exception(f"Error : check_name_list Method - {e}")
        print(f"Error : check_name_list Method -{e}")

# /add_name command
async def block_fake_twitter(update: Update, context: CallbackContext):
    try:
        query = update.callback_query
        parts = query.data.split('_',1) # Split at the first underscore only
        action = parts[0]
        hash_id = parts[1]
        if action == 'yesBlock':
            if len(hash_id) == 0:
                print("Thre is no linked twitter")
                logging.info("Thre is no linked twitter")
                return
            data = MessageIdBasedOnTwitter.check_twitter_handle_exists_from_hashcode(hash_id)
            if data:
                twitter = data["twitter"]
                check = FakeTwitterAccounts.is_Fake(twitter)
                if check:
                    #Send Already Blocked button
                    keyboard = [InlineKeyboardButton("Already Blocked", callback_data="abcabcde_")],
                
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_reply_markup(reply_markup=reply_markup)
                    return
                
                else:
                    add_status = FakeTwitterAccounts.add_account(twitter)
                    if add_status:
                        #Send Blocked sucess button
                        keyboard = [InlineKeyboardButton("Blocked Success", callback_data="abcabcde_")],
                        
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await query.edit_message_reply_markup(reply_markup=reply_markup)
                        data = MessageIdBasedOnTwitter.check_twitter_handle_exists_from_twitter_link(twitter)
                        if data:
                            delete_message(Config.GROUP2_ID,data["message_id"])
                            delete_message(Config.GROUP2_ID,data["empty_msg_id"])
                            MessageIdBasedOnTwitter.delete_message(twitter)
                            
                    else:

                        keyboard = [
                            [InlineKeyboardButton("Error Happened (PRESS AGAIN)", callback_data=f"block_{hash_id}")]
                        ]

                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await query.edit_message_reply_markup(reply_markup=reply_markup)

            else:

                keyboard = [
                    [InlineKeyboardButton("Error Happened (PRESS AGAIN)", callback_data=f"block_{hash_id}")]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_reply_markup(reply_markup=reply_markup)

        elif action=='noBlock':
            keyboard = [
                    [InlineKeyboardButton("BLOCK TWITTER", callback_data=f"block_{hash_id}")]
                ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_reply_markup(reply_markup=reply_markup)

    except Exception as e:
        logging.exception(f"Error in add_fake_twitter_into_database def{e}")
        print(f"Error in add_fake_twitter_into_database def {e}")


# Handle yes No button press
async def yes_no_button(update: Update, context: CallbackContext):
    try:
        query = update.callback_query
        parts = query.data.split('_',1) # Split at the first underscore only
        action = parts[0]
        
        if action=="block":
            hash_id = parts[1]
            # Ask for confirmation to delete the token name
            keyboard = [
                [InlineKeyboardButton("Yes", callback_data=f"yesBlock_{hash_id}")],
                [InlineKeyboardButton("No", callback_data=f"noBlock_{hash_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_reply_markup(reply_markup=reply_markup)

        elif action =="delete" :
        
            token_name = parts[1]
            # Ask for confirmation to delete the token name
            keyboard = [
                [InlineKeyboardButton("Yes", callback_data=f"yesDelete_{token_name}")],
                [InlineKeyboardButton("No", callback_data=f"noDelete_{token_name}")]
            ]
        
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"Do you want to DELETE the token name '{token_name}'?", reply_markup=reply_markup)


    except Exception as e:
        logging.exception(f"Error : yes_no_button method{e}")
        print(f"Error : yes_no_button Method {e}")



# /check_duplicate_count command
async def check_duplicate_count(update: Update, context: CallbackContext):
    await update.message.reply_text(f"*Duplicate count is {Config.DEFAULT_MULTIPLICITY_VALUE}*", parse_mode='Markdown')
    

# /set_duplicate_count command
async def set_duplicate_count(update: Update, context: CallbackContext):
    try:
        user_id = str(update.message.from_user.id)
        group_id = str(update.message.chat.id)

        if user_id == Config.ADMIN_ID and group_id==Config.ADMIN_ID:
            if len(context.args) == 0:
                send_telegram_message_to_admin("*Please provide a number as this* `/set_duplicate_count` number.", parse_mode='Markdown')
                return

            entered_value = context.args[0]

            # Check if entered value is a valid number
            if not entered_value.isdigit():  # Checks if it's a whole number (non-negative)
                send_telegram_message_to_admin(f"'{entered_value}' is not a valid number. Please provide a valid number with the comand.", parse_mode='Markdown')
                return

            # If it's a number, set the duplicate_count
            Config.DEFAULT_MULTIPLICITY_VALUE = int(entered_value)
            send_telegram_message_to_admin(f"Duplicate count has been set to {Config.DEFAULT_MULTIPLICITY_VALUE}.", parse_mode='Markdown')
    
    except Exception as e:
        logging.exception(f"Error : set_duplicate_count method{e}")
        print(f"Error : set_duplicate_count Method {e}")

# /check_genuine_token_display_count command
async def check_genuine_token_display_count(update: Update, context: CallbackContext):
    await update.message.reply_text(f"*Genuine Tokens Display count is {Config.GENUINE_TOKEN_DISPLAY_COUNT}*", parse_mode='Markdown')
    

# /set_genuine_token_display_count command
async def set_genuine_token_display_count(update: Update, context: CallbackContext):
    try:
        user_id = str(update.message.from_user.id)
        group_id = str(update.message.chat.id)

        if user_id == Config.ADMIN_ID and group_id==Config.ADMIN_ID:        
            if len(context.args) == 0:
                send_telegram_message_to_admin("*Please provide a number as this* `/set_genuine_display_count` number.", parse_mode='Markdown')
                return

            entered_value = context.args[0]

            # Check if entered value is a valid number
            if not entered_value.isdigit():  # Checks if it's a whole number (non-negative)
                send_telegram_message_to_admin(f"'{entered_value}' is not a valid number. Please provide a valid number with the comand.", parse_mode='Markdown')
                return

            # If it's a number, set the duplicate_count
            Config.GENUINE_TOKEN_DISPLAY_COUNT = int(entered_value)
            send_telegram_message_to_admin(f"Genuine Tokens Display count has been set to {Config.GENUINE_TOKEN_DISPLAY_COUNT}.", parse_mode='Markdown')
        
    except Exception as e:
        logging.exception(f"Error : set_genuine_token_display_count method{e}")
        print(f"Error : set_genuine_token_display_count Method {e}")


# /set_genuine_token_display_count command
async def check_contract_address(update: Update, context: CallbackContext):
    try:
        user_id = str(update.message.from_user.id)
        group_id = str(update.message.chat.id)

        if user_id == Config.ADMIN_ID and group_id==Config.ADMIN_ID:
            contract_address = update.message.text
            #print(len(contract_address))

            if len(contract_address) == 44:
                coin = MemeCoins.get_tokens_by_contract_address(contract_address)

            if coin:
                # Unpack result into individual variables
                id = coin.id
                created_at = coin.created_at
                signature = coin.signature
                token_name = coin.token_name
                token_ticker = coin.token_ticker
                dev_address = coin.dev_address
                initial_buy = coin.initial_buy
                sol_amount = coin.sol_amount
                bonding_curve_key = coin.bonding_curve_key
                v_tokens_in_bonding_curve = coin.v_tokens_in_bonding_curve
                v_sol_in_bonding_curve = coin.v_sol_in_bonding_curve
                market_cap_sol = coin.market_cap_sol
                metadata_link = coin.metadata_link
                twitter_link = coin.twitter_link


                meta_data = methods.get_ipfs_metadata(metadata_link)

                image_link = meta_data.get("image", None) if meta_data else None
                if image_link:
                    new_image_url= image_link
                else:
                    new_image_url = f"https://pump.fun/coin/{contract_address}"
                
                twitter_url_string ="\n\n🐦 *NO TWITTER ADDED* 🐦"
                if twitter_link !="no":
                    twitter_user_name_string= f"{methods.escape_markdown(twitter_link.split('/')[-1])}"
                    twitter_url_string=f"[🐦]({twitter_link}) - @{twitter_user_name_string}"

                current_sol_value =methods.get_current_sol_value() 
                market_cap_in_usd = market_cap_sol *current_sol_value

                message = f"""
                [🚨]({new_image_url}) Available 🚨\n\n`{token_name}` (`{token_ticker}`)\n\n{contract_address}\n\n[💊](https://pump.fun/coin/{contract_address}) [🙋‍♂️](https://solscan.io/account/{dev_address}) [🔍](https://solscan.io/token/{contract_address}) {twitter_url_string}
                \n-----------------------------------------
                \n🕒 *Created At* : {methods.time_since_added(created_at)}
                \n🪙 *Initial Buy* : {f"{round(initial_buy,0):,}"}
                \n💵 *SOL amount* : {f"{round(sol_amount,2):,}"} *SOL*
                \n🏦 *Tokens InCurve* : {f"{round(v_tokens_in_bonding_curve,2):,}"}
                \n🏦 *SOL InCurve*: {f"{round(v_sol_in_bonding_curve,2):,}"}
                \n💰 *MC* : {f"{round(market_cap_in_usd,2):,}"} *USD* ({round(market_cap_sol,2):,} *SOL*)
                \n-----------------------------------------
                """
                send_telegram_message_to_admin(message, parse_mode='Markdown')

    except Exception as e:
        logging.exception(f"Error : check_contract_address method{e}")
        print(f"Error : check_contract_address Method {e}")



# /status command
terminate_status = False
async def terminate_the_programme(update: Update, context: CallbackContext):
    try:
        global terminate_status
    
        user_id = str(update.message.from_user.id)
        group_id = str(update.message.chat.id)

        if user_id == Config.ADMIN_ID and group_id==Config.ADMIN_ID:
            if len(context.args) == 0:
                send_telegram_message_to_admin("*Are you sure to terminate the copy this and message* `/terminate yes`.", parse_mode='Markdown')
                return

            terminate = context.args[0]
    
            print(terminate_status)
            if terminate_status:
                if terminate == "yes" and terminate_status:
                    terminate = "no"
                    # Some code...
                    message= "Terminate the program within 5 second (stopped running code)"
                    send_telegram_message_to_admin(message, parse_mode='Markdown')
                    send_telegram_message_to_users(message,Config.GROUP1_ID, parse_mode='Markdown')

                    time.sleep(5)
                    print("Terminated the proggrame")
                    logging.info("Terminated the proggrame")
                    #Exit the script
                    sys.exit()

                    message= "Error - Terminate unsuccessfull\nPrograme is still running"
                    send_telegram_message_to_admin(message, parse_mode='Markdown')
                    send_telegram_message_to_users(message,Config.GROUP1_ID, parse_mode='Markdown')
                    print("Error - Terminate unsuccessfull. Programe is still running")
                    logging.info("Error - Terminate unsuccessfull. Programe is still running")

                else:
                    send_telegram_message_to_admin(f"invalid input. copy and send this command `/terminate yes`")
                    
            terminate_status = True

    except Exception as e:
        logging.exception(f"Error : set_genuine_token_display_count method{e}")
        print(f"Error : set_genuine_token_display_count Method {e}")



# Main function to set up the Telegram bot
async def run_telegram_bot():
    application = Application.builder().token(Config.TELEGRAM_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("add_name", add_name))
    application.add_handler(CommandHandler("name_list", check_name_list))
    application.add_handler(CommandHandler("check_duplicate_count", check_duplicate_count))
    application.add_handler(CommandHandler("set_duplicate_count", set_duplicate_count))
    application.add_handler(CommandHandler("terminate", terminate_the_programme))
    application.add_handler(CommandHandler("check_genuine_display_count", check_genuine_token_display_count))
    application.add_handler(CommandHandler("set_genuine_display_count", set_genuine_token_display_count))
    application.add_handler(CommandHandler("add_fake_twitter", block_fake_twitter))

    # Add a handler that will react only to text messages (excluding commands)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_contract_address))


    # Register callback handlers
    application.add_handler(CallbackQueryHandler(yes_no_button, pattern="^delete_|^block_"))
    application.add_handler(CallbackQueryHandler(delete_token, pattern="^yesDelete_|^noDelete_"))
    application.add_handler(CallbackQueryHandler(block_fake_twitter, pattern="^yesBlock_|^noBlock_" ))

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

