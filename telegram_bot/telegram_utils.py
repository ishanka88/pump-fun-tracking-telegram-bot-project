
import requests  # Use an async HTTP library
import json
from config import Config
import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton 

def send_telegram_message_to_admin(message, parse_mode='HTML'):
    try:
        url = f'https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendMessage'
        params = {
            'chat_id': Config.ADMIN_ID,
            'text': message,
            'parse_mode': parse_mode
        }
        response = requests.get(url, params=params)
        #print(f"Sent to {Config.ADMIN_ID}, Response: {response.json()}")
        return response
            
    except Exception as e:
        # Log and print network-related errors
        error_message = f"Network error occurred while sending message to chat_id {Config.ADMIN_ID}: {e}"
        logging.error(error_message)
        print(error_message)
        return False


def send_telegram_message_to_users(message, chat_id, parse_mode='HTML', reply_markup=None):
   
    try:
        url = f'https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendMessage'
        
        params = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode
        }

        if reply_markup:
            # Ensure the reply_markup is serialized as JSON
            if isinstance(reply_markup, InlineKeyboardMarkup):
                params['reply_markup'] = json.dumps(reply_markup.to_dict())
            else:
                params['reply_markup'] = json.dumps(reply_markup)

    
        # Use POST request to send the message
        response = requests.post(url, data=params)

        # Check if the message was successfully sent
        if response.status_code == 200:
            print(f"Message sent to chat_id {chat_id}")
            message_id = response.json()["result"]["message_id"]
            return True, message_id
        else:
            # Log detailed error information
            error_message = f"Failed to send message to chat_id {chat_id}, " \
                            f"Error: {response.status_code}, {response.text}"
            logging.error(error_message)
            print(error_message)
            return False, None
    except requests.exceptions.RequestException as e:
        # Log and print network-related errors
        error_message = f"Network error occurred while sending message to chat_id {chat_id}: {e}"
        logging.error(error_message)
        print(error_message)
        return False, None
    



def delete_message(chat_id, message_id):
    url = f'https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/deleteMessage'
    
    # Prepare the parameters (chat_id and message_id)
    params = {
        'chat_id': chat_id,
        'message_id': message_id
    }

    # Send the delete request
    response = requests.post(url, params=params)
    
    # Check the response and print if the deletion was successful
    if response.json().get('ok'):
        print(f"Message with ID {message_id} deleted successfully.")
    else:
        print(f"Failed to delete message with ID {message_id}. Response: {response.json()}")
