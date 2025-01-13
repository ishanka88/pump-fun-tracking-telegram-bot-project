# semaphore.py

import asyncio
from config import Config

 # Adjust the number as needed
semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_TASKS)
