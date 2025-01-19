
import os

class Config:
    TELEGRAM_TOKEN = '7252788699:AAFjymiBcna1CZXYnpeB2EtVCJmeaXlxYUY'

    ADMIN_ID = '1813173704'
    GROUP1_ID = "-1002261635931"
    GROUP2_ID = "-004607352219"
    WEBSOCKET_URI = 'wss://pumpportal.fun/api/data'
    MAX_CONCURRENT_TASKS = int(os.getenv('MAX_CONCURRENT_TASKS', 5))  # Default to 5 if not set

    #variables
    DEFAULT_MULTIPLICITY_VALUE = 4
    GENUINE_TOKEN_DISPLAY_COUNT = 5
    MARKETCAP_LIMIT = 20000
    TOKEN_NAMES_LIST = None
    
    # Sol Vakue in usd
    CURRENT_SOL_VALUE = 180