
import requests  # Use an async HTTP library

TELEGRAM_TOKEN = '7252788699:AAFjymiBcna1CZXYnpeB2EtVCJmeaXlxYUY'
CHAT_IDS = ['1813173704']  

def send_telegram_message_to_bot(message, parse_mode='HTML'):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    for chat_id in CHAT_IDS:
        params = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        response = requests.get(url, params=params)
        
def send_telegram_message(message,chat_id, parse_mode='HTML'):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    
    params = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': parse_mode
    }

    # Make the request to the Telegram API
    response = requests.get(url, params=params)

    # Check if the message was successfully sent
    if response.status_code == 200:
        print(f"Message sent to chat_id {chat_id}")
       
    else:
        print(f"Failed to send message to chat_id {chat_id}, Error: {response.status_code}, {response.text}")
        print (message)