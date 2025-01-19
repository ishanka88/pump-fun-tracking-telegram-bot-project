
import logging
import asyncio
import requests
import Levenshtein
import logging
from config import Config
from telegram_bot.telegram_utils import send_telegram_message_to_users, send_telegram_message_to_admin, delete_message
from semaphore import semaphore
from website.models import MemeCoins,FakeTwitterAccounts,MessageIdBasedOnTwitter
from collections import Counter
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
from time import time
from datetime import datetime
import hashlib


def get_current_sol_value():
    try:
        # Define the CoinGecko API URL for fetching Solana price
        url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"

        # Send GET request to the API
        response = requests.get(url)

        # Parse the response JSON
        data = response.json()

        # Extract the current price of SOL in USD
        sol_price = data["solana"]["usd"]
        Config.CURRENT_SOL_VALUE = sol_price
        return Config.CURRENT_SOL_VALUE
        print(f"The current price of Solana (SOL) is: ${sol_price}")
    except requests.RequestException as e:
        print(f"An error occurred get_current_sol_value: {e}")
        logging.exception("An error occurred get_current_sol_value : %s", str(e))
        return Config.CURRENT_SOL_VALUE

################################################
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
    
#######################################################

def get_match_percentage(str1, str2):
    distance = Levenshtein.distance(str1.lower(), str2.lower())
    max_len = max(len(str1), len(str2))
    if max_len == 0:
        return 100
    match_percentage = (1 - distance / max_len) * 100
    return int(match_percentage)

#########################################################


def get_unique_tokens(tokens_list):
    try:
        # Check if the items in the list are instances of MemeCoins (SQLAlchemy models)
        if isinstance(tokens_list[0], MemeCoins):
            # Extract all dev_address values using dot notation if they are MemeCoins objects
            dev_addresses = [token.dev_address for token in tokens_list]
        else:
            # Assume the items are dictionaries and access dev_address using subscript notation
            dev_addresses = [token["dev_address"] for token in tokens_list]

        # Count occurrences of each dev_address using Counter
        dev_address_counts = Counter(dev_addresses)

        # Filter out dev_addresses that appear only once
        unique_dev_addresses = [dev_address for dev_address, count in dev_address_counts.items() if count == 1]

        # Get tokens that have these unique dev_addresses
        if isinstance(tokens_list[0], MemeCoins):
            # If the list contains MemeCoins objects, use dot notation
            unique_tokens = [token for token in tokens_list if token.dev_address in unique_dev_addresses]
        else:
            # If the list contains dictionaries, use subscript notation
            unique_tokens = [token for token in tokens_list if token["dev_address"] in unique_dev_addresses]

        return unique_tokens

    except Exception as e:
        logging.error(f"Error get_unique_tokens: {e}")
        print(f"Error get_unique_tokens: {e}")
        return []


##########################################################

def time_since_added(created_at):
    try:
        # Get the current time in UTC
        now = datetime.utcnow()

        # Calculate the time difference
        time_diff = now - created_at

        # Convert time_diff to seconds
        totall_seconds = time_diff.total_seconds()

        # Convert seconds into more readable units
        days = totall_seconds // (24 * 3600)
        hours = (totall_seconds % (24 * 3600)) // 3600
        minutes = (totall_seconds % 3600) // 60
        seconds = int(totall_seconds % 60)  # Convert to integer to avoid float display

        # Build the time string conditionally based on non-zero values
        time_parts = []
        if totall_seconds > 3:
            if days > 0:
                time_parts.append(f"{int(days)}d")
            if hours > 0:
                time_parts.append(f"{int(hours)}h")
            if minutes > 0:
                time_parts.append(f"{int(minutes)}m")
            elif seconds > 0:  # Only show seconds if minutes are zero
                time_parts.append(f"{seconds}s")
        else:
            time_parts.append("NOW 🟢")
        # Join the parts into a single string and return
        time_str = " ".join(time_parts)

        return time_str
    
    except Exception as e:
        logging.error(f"Error in time_since_added method: {e}")
        print(str(e))
        return "Error in calculating time"

#################################################################################

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



#####################################################################################
######################################################################################

async def add_token_data_into_database(token_name, token_ticker, contract_address, dev_address, metadata_link
                                       ,initial_buy, sol_amount, bonding_curve_key, v_tokens_in_bonding_curve
                                        ,v_sol_in_bonding_curve, market_cap_sol, signature):
    
    try:
        async with semaphore:

            data = get_ipfs_metadata(metadata_link)
            twitter_link = data.get("twitter", "no") if data else "no"

            status = MemeCoins.add_meme_coin(token_name, token_ticker, contract_address, dev_address, 
                                             metadata_link, twitter_link,initial_buy, sol_amount, 
                                             bonding_curve_key, v_tokens_in_bonding_curve,v_sol_in_bonding_curve, 
                                             market_cap_sol, signature)
            if not status:
                logging.warning(f"Failed to add token {token_name} to the database.")

            if twitter_link != "no":
                asyncio.create_task(send_telegram_message_if_same_twitter_connected(twitter_link,token_ticker,token_name,contract_address))


    except Exception as e:
        print("Error adding token data to database: {e}")
        logging.error(f"Error adding token data to database: {e}")


#####################################################################################
######################################################################################
async def send_telegram_message_if_same_twitter_connected(twitter_link,token_ticker,token_name,contract_address):
    try:
        async with semaphore:
            tokens_list=MemeCoins.get_tokens_have_same_twitter(twitter_link)
            total_tokens_count=len(tokens_list)
            if total_tokens_count >=Config.DEFAULT_MULTIPLICITY_VALUE :
                
                check= FakeTwitterAccounts.is_Fake(twitter_link)
                if check:
                    print(f"Fake Found - {twitter_link}")
                    logging.info(f"Fake Found - {twitter_link}")
                    return
                
                unique_tokens_list=get_unique_tokens(tokens_list)

                send_telegram_message_if_found_a_trending_token(unique_tokens_list,total_tokens_count,token_ticker,token_name,contract_address,Config.GROUP2_ID,twitter_link)
                
    except Exception as e:
        print("Error send_telegram_message_if_same_twitter_connected: {e}")
        logging.error(f"Error send_telegram_message_if_same_twitter_connected: {e}")


#####################################################################################
####################################################################################

async def check_token_name_available_in_the_list_and_send_telegram_message (token_name,token_symbol,contract_address,developer,url_link):

    try:
        async with semaphore:
            for name in Config.TOKEN_NAMES_LIST:
                if name.lower() in token_name.lower() or name.lower() in token_symbol.lower():
                    match_percentage_token_name = get_match_percentage(name, token_name)
                    match_percentage_token_symbol = get_match_percentage(name, token_symbol)

                    meta_data = get_ipfs_metadata(url_link)

                    image_link = meta_data.get("image", None) if meta_data else None
                    if image_link:
                        new_image_url= image_link
                    else:
                        new_image_url = f"https://pump.fun/coin/{contract_address}"
                        
                    twitter_url = meta_data.get("twitter", None) if meta_data else None

                    if twitter_url :
                        return
                        # twitter_url_string = f" [🐦]({twitter_url})Twitter"

                    # Using escape_markdown with None values now handled properly
                    website_url = meta_data.get("website", None) if meta_data else None
                    telegram_url = meta_data.get("telegram", None) if meta_data else None

                    website_url_string =""
                    telegram_url_string =""

                    if website_url :
                        website_url_string = f" [🌐]({website_url}) Website" 

                    if telegram_url :
                        telegram_url_string = f" [📱]({telegram_url})Telegram" 

                    empty_message = "\n⭕\n"
                    send_telegram_message_to_admin(empty_message, parse_mode='Markdown')

                    message = f"""
                    [🚨]({new_image_url}) *{name}* 🚨\n\n`{token_name}` (`{token_symbol}`)\n\nName    - {match_percentage_token_name} %\nSymbol - {match_percentage_token_symbol} %\n\n📝 Contract Address: [🔍](https://solscan.io/token/{contract_address})\n`{contract_address}`\n\n🙋‍♂️ Deployer: [🔗](https://solscan.io/account/{developer})\n{developer}\n\n[🔍](https://solscan.io/token/{contract_address}) Solscan     [💊](https://pump.fun/coin/{contract_address}) PumpFun
                    \n{website_url_string}    {telegram_url_string}
                    \n🐦 *NO TWITTER ADDED* 🐦"
                    """
                    send_telegram_message_to_admin(message, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Error checking tokens and sending message: {e}")


#####################################################################################
#####################################################################################

async def check_same_token_availability_in_database(token_name, token_symbol,contract_address):
    try:
        async with semaphore:
            availability = MemeCoins.check_token_availability(token_name, token_symbol,Config.DEFAULT_MULTIPLICITY_VALUE)

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


                send_telegram_message_if_found_a_trending_token(unique_tokens,total_tokens_count,token_symbol,token_name,contract_address, Config.GROUP1_ID)
    
    except Exception as e:
        logging.error(f"Error checking token availability: {e}")


##################################################################################
###################################################################################



def send_telegram_message_if_found_a_trending_token(unique_tokens,total_tokens_count,token_symbol,token_name,contract_address,groupId,twitter=None):

    try:
        reply_markup=None
        main_twitter_str = ""
        already_exit =""
        twitter_hash_id=""

        if twitter :
            main_twitter_str =f" \n\n[🐦]({twitter}) Twitter - @{escape_markdown(twitter.split('/')[-1])}"
            already_exit = MessageIdBasedOnTwitter.check_twitter_handle_exists_from_twitter_link(twitter.lower())

            if already_exit :
                twitter_hash_id = already_exit["hash_id"]
            else:
                twitter_hash_id = hashlib.md5(twitter.encode()).hexdigest()

            keyboard = [
                    [InlineKeyboardButton("BLOCK TWITTER", callback_data=f"block_{twitter_hash_id}")]
                ]
            reply_markup = InlineKeyboardMarkup(keyboard)


        new_image_url = f"https://pump.fun/coin/{contract_address}"
        genuine_or_not = "❌"
        
        unique_tokens_count = len(unique_tokens)
        if not len (unique_tokens)==0:
            genuine_list_string =f"⤵️⤵️ *Genuine  List ({unique_tokens_count}/{total_tokens_count})* ⤵️⤵️ \nLATEST {Config.GENUINE_TOKEN_DISPLAY_COUNT} 👇"
            i=0
            for token in unique_tokens[0:Config.GENUINE_TOKEN_DISPLAY_COUNT] :
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
                g_created_at = token.get("created_at")

                created_time_from_now = time_since_added(g_created_at)

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


                genuine_list_string = genuine_list_string + f"""\n\n*{f"{i:02d}" if i < 10 else str(i)}*. `{g_token_name}`(`{g_token_ticker}`)\n  Created Time -{created_time_from_now}\n  [💊](https://pump.fun/coin/{g_contract_address}) [📝](https://solscan.io/token/{g_contract_address}) [🙋‍♂️](https://solscan.io/account/{g_dev_address}){website_url_string}{telegram_url_string}{twitter_url_string}{twitter_user_name_string} """
                    
        else:
            genuine_list_string ="⤵️⤵️ *GENUINE LIST* ⤵️⤵️\n\n   No Genuine Tokens ❌"
        

        if total_tokens_count == Config.DEFAULT_MULTIPLICITY_VALUE:
            topic =f"[😍]({new_image_url}) *New Trending Token Found* 😍"
        else:
            topic = f"[🔥]({new_image_url}) *New Update* 🔥"

        main_message = f"""

        {topic}\n\n`{escape_markdown(token_name)}` (`{escape_markdown(token_symbol)}`) {genuine_or_not}\n\n`{contract_address}`{main_twitter_str}\n\nMultiplicity : *{total_tokens_count}*  (default {Config.DEFAULT_MULTIPLICITY_VALUE})\n\n✔️ *{unique_tokens_count} Genuine* | ❌  *{total_tokens_count - unique_tokens_count } Fake*\n\n{genuine_list_string}\n\n..."""

        # SEND MESSAGES
        empty_message = "\n⭕\n"
        empty_msg_response=send_telegram_message_to_users(empty_message, groupId,parse_mode='Markdown')

        main_response = send_telegram_message_to_users(main_message, groupId, parse_mode='Markdown', reply_markup=reply_markup)


        if twitter and main_response[0]:

            message_id = main_response[1]
            empty_msg_id = empty_msg_response[1]
            if already_exit:
               # If the record exists, extract message_id and multiple_count
                pre_msg_id = already_exit["message_id"]
                pre_empty_msg_id = already_exit["empty_msg_id"]
                pre_multiple_count = already_exit["multiple_count"]

                delete_message(groupId, pre_empty_msg_id)
                delete_message(groupId, pre_msg_id)
                
                new_multiple_count =pre_multiple_count+1

                MessageIdBasedOnTwitter.update_message_and_count_and_hasah_id(twitter,new_multiple_count,message_id,empty_msg_id)
            
            else:
                multiple_count = Config.DEFAULT_MULTIPLICITY_VALUE
                MessageIdBasedOnTwitter.add_message_details(twitter.lower(),message_id,empty_msg_id,twitter_hash_id,multiple_count)

    except Exception as e:
        print(f"Error send_telegram_message_if_found_a_trending_token method: {e}")
        logging.error(f"Error send_telegram_message_if_found_a_trending_token method: {e}")

##############################################################################


def send_telegram_message_if_given_token_name_available_in_database(already_available_tokens_list,token_name):

    try:
        if already_available_tokens_list:
            new_image_url=""
            already_available_tokens_count = len(already_available_tokens_list)
            unique_tokens = get_unique_tokens(already_available_tokens_list)
            if unique_tokens :
                unique_tokens_count = len(unique_tokens)
                twitter_unavailabale_string =f""
                i=0
                for token in unique_tokens:
                    twitter = token.twitter_link
                    if twitter == "no":
                        i=1+1
                        g_token_name = escape_markdown(token.token_name)
                        g_token_ticker = escape_markdown(token.token_ticker)
                        g_contract_address = token.contract_address
                        g_dev_address = token.dev_address
                        g_metadata_link = token.metadata_link
                        g_created_at = token.created_at

                        created_time_from_now = time_since_added(g_created_at)

                        meta_data =get_ipfs_metadata(g_metadata_link)

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


                        if i==1:
                            image_link = meta_data.get("image", None) if meta_data else None
                            if image_link:
                                new_image_url= image_link
                            else:
                                new_image_url = f"https://pump.fun/coin/{g_contract_address}"


                        
                        twitter_unavailabale_string = twitter_unavailabale_string + f"""\n\n*{f"{i:02d}" if i < 10 else str(i)}*. `{g_token_name}`(`{g_token_ticker}`)\n  Created Time -{created_time_from_now}\n  [💊](https://pump.fun/coin/{g_contract_address}) [📝](https://solscan.io/token/{g_contract_address}) [🙋‍♂️](https://solscan.io/account/{g_dev_address}){website_url_string}{telegram_url_string}{twitter_url_string}{twitter_user_name_string} """

                genuine_list_string =f"⤵️⤵️ *Without Twitter ({i}/{unique_tokens_count})* ⤵️⤵️\n\n{twitter_unavailabale_string}"

            else:
                genuine_list_string ="⤵️⤵️ *Without Twitter* ⤵️⤵️\n\n   No Twitter added Tokens ❌"
            

            topic = f"[🔥]({new_image_url}) *TOKEN AVAILABILE* 🔥"

            main_message = f"""{topic}\n\nName :{token_name}\n\nMultiplicity : *{already_available_tokens_count}*\n\n✔️ *{unique_tokens_count} Genuine* | ❌  *{already_available_tokens_count - unique_tokens_count } Fake*\n\n{genuine_list_string}\n\n..."""

            send_telegram_message_to_admin(main_message, parse_mode='Markdown')

    except Exception as e:
        print(f"Error send_telegram_message_if_given_token_name_available_in_database method: {e}")
        logging.error(f"Error send_telegram_message_if_given_token_name_available_in_database method: {e}")


##################################################################################################

async def check_marketcap_is_grater_than_the_limit_and_send_telegrm_message(contract_address,market_cap_sol):
    try:

        market_cap_in_usd = market_cap_sol * Config.CURRENT_SOL_VALUE

        if market_cap_in_usd >= Config.MARKETCAP_LIMIT:

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


                meta_data = get_ipfs_metadata(metadata_link)

                image_link = meta_data.get("image", None) if meta_data else None
                if image_link:
                    new_image_url= image_link
                else:
                    new_image_url = f"https://pump.fun/coin/{contract_address}"
                
                twitter_url_string ="\n\n🐦 *NO TWITTER ADDED* 🐦"
                if twitter_link !="no":
                    twitter_user_name_string= f"{escape_markdown(twitter_link.split('/')[-1])}"
                    twitter_url_string=f"[🐦]({twitter_link}) - @{twitter_user_name_string}"

                main_message = f"""
                [🚨]({new_image_url}) Available 🚨\n\n`{token_name}` (`{token_ticker}`)\n\n{contract_address}\n\n[💊](https://pump.fun/coin/{contract_address}) [🙋‍♂️](https://solscan.io/account/{dev_address}) [🔍](https://solscan.io/token/{contract_address}) {twitter_url_string}
                \n-----------------------------------------
                \n🕒 *Created At* : {time_since_added(created_at)}
                \n🪙 *Initial Buy* : {f"{round(initial_buy,0):,}"}
                \n💵 *SOL amount* : {f"{round(sol_amount,2):,}"} *SOL*
                \n🏦 *Tokens InCurve* : {f"{round(v_tokens_in_bonding_curve,2):,}"}
                \n🏦 *SOL InCurve*: {f"{round(v_sol_in_bonding_curve,2):,}"}
                \n💰 *MC* : {f"{round(market_cap_in_usd,2):,}"} *USD* ({round(market_cap_sol,2):,} *SOL*)
                \n-----------------------------------------
                """

                groupId = Config.GROUP1_ID
                
                        # SEND MESSAGES
                empty_message = "\n⭕\n"
                empty_msg_response=send_telegram_message_to_users(empty_message, groupId ,parse_mode='Markdown')

                main_response = send_telegram_message_to_users(main_message, groupId, parse_mode='Markdown')

    except Exception as e:
        logging.exception(f"Error : check_marketcap_is_grater_than_the_limit_and_send_telegrm_message method{str(e)}")
        print(f"Error : check_marketcap_is_grater_than_the_limit_and_send_telegrm_message Method {str(e)}")