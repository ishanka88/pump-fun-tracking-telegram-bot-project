
import logging
import asyncio
import requests
import Levenshtein
import logging
from config import Config
from telegram_bot.telegram_utils import send_telegram_message, send_telegram_message_to_bot
from semaphore import semaphore
from website.models import MemeCoins
from collections import Counter
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker


#############################################
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
    # Extract all dev_address values
    dev_addresses = [token["dev_address"] for token in tokens_list]

    # Count occurrences of each dev_address using Counter
    dev_address_counts = Counter(dev_addresses)

    # Filter out dev_addresses that appear only once
    unique_dev_addresses = [dev_address for dev_address, count in dev_address_counts.items() if count == 1]

    # Get tokens that have these unique dev_addresses
    unique_tokens = [token for token in tokens_list if token["dev_address"] in unique_dev_addresses]

    return unique_tokens

##########################################################

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

#############################################################

async def check_same_token_availability(token_name, token_symbol,contract_address):
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

###########################################################

async def check_token_name_available_in_the_list_and_send_telegram_message (token_name,token_symbol,contract_address,developer,url_link):
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

###################################################################################

async def checking_tokens_from_token_list_and_send_telegram_message (token_name,token_symbol,contract_address,developer,url_link):

    try:
        async with semaphore:
            for name in Config.TOKEN_NAMES_LIST:
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


##################################################################################

def send_telegram_message_if_found_a_trending_token(unique_tokens,total_tokens_count,token_symbol,token_name,contract_address,groupId):
    
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

    {topic}\n\n`{escape_markdown(token_name)}` (`{escape_markdown(token_symbol)}`) {genuine_or_not}\n\nCA-`{contract_address}`\n\nMultiplicity : *{total_tokens_count}*  (default {Config.DEFAULT_MULTIPLICITY_VALUE})\n\n✔️ *{unique_tokens_count} Genuine* | ❌  *{total_tokens_count - unique_tokens_count } Fake*\n\n{genuine_list_string}\n\n..."""

    empty_message = "\n⭕\n"
    send_telegram_message(empty_message, groupId,parse_mode='Markdown')

    send_telegram_message(main_message,groupId, parse_mode='Markdown')

##############################################################################

async def send_telegram_message_if_same_twitter_connected(twitter_link,token_symbol,token_name,contract_address):
    try:
        async with semaphore:
            tokens_list=MemeCoins.get_tokens_have_same_twitter(twitter_link)
            total_tokens_count=len(tokens_list)
            if total_tokens_count >=Config.DEFAULT_MULTIPLICITY_VALUE :
                unique_tokens_list=get_unique_tokens(tokens_list)
                send_telegram_message_if_found_a_trending_token(unique_tokens_list,total_tokens_count,token_symbol,token_name,contract_address,Config.GROUP2_ID)
                
    except Exception as e:
        logging.error(f"Error adding token data to database: {e}")

##############################################################

def time_since_added(created_at):
    try:
        # Get the current time in UTC
        now = datetime.utcnow()

        # Calculate the time difference
        time_diff = now - created_at

        # Convert time_diff to seconds
        seconds = time_diff.total_seconds()

        # Convert seconds into more readable units
        days = seconds // (24 * 3600)
        hours = (seconds % (24 * 3600)) // 3600
        minutes = (seconds % 3600) // 60
        seconds = int(seconds % 60)  # Convert to integer to avoid float display

        # Build the time string conditionally based on non-zero values
        time_parts = []
        if not seconds ==0:
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
