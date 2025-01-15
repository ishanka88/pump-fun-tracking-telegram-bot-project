from flask import Blueprint
from telegram_bot.telegram_utils import send_telegram_message_to_admin
from website.models import TrackingTokenNames
import asyncio
import json

views = Blueprint('views', __name__)

# # /subscribe command: Subscribe to token creation events
# async def subscribe():
#     token_names = TrackingTokenNames.get_all_tokens()
#     if len(token_names) == 0:
#         send_telegram_message('Please add token names to the list before subscribing.')
#         return

#     async def subscribe_to_tokens():
#         uri = 'wss://pumpportal.fun/api/data'
#         async with websockets.connect(uri) as ws:
#             print('Subscribing to new token creation events...')
#             payload = {'method': 'subscribeNewToken'}
#             await ws.send(json.dumps(payload))

#             while True:
#                 message = await ws.recv()
#                 data = json.loads(message)
#                 token_name = data.get('name', '')
#                 token_symbol = data.get('symbol', '')
#                 for name in token_names:
#                     if name.lower() in token_name.lower() or name.lower() in token_symbol.lower():
#                         contract_address = data.get('mint', '')
#                         developer = data.get('traderPublicKey', '')
#                         url_link = data.get('uri', '')
#                         send_telegram_message(f'New token created: {token_name} ({token_symbol})')
    
#     asyncio.create_task(subscribe_to_tokens())
