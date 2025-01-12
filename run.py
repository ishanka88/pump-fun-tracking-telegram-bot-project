import asyncio
import threading
import logging
import nest_asyncio
from logging.handlers import RotatingFileHandler
from website import app  # Flask app
from telegram_bot.bot import run_telegram_bot  # Your Telegram bot logic
from werkzeug.serving import make_server

# Set up log rotation
handler = RotatingFileHandler('app.log', maxBytes=50*1024*1024, backupCount=3)
handler.setLevel(logging.DEBUG)

# Set log format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logging.getLogger().addHandler(handler)

# Configure logging for the application
logging.basicConfig(
    level=logging.DEBUG,          # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

# # Example logging messages
# logging.debug("This is a debug message")
# logging.info("This is an info message")
# logging.warning("This is a warning message")
# logging.error("This is an error message")
# logging.critical("This is a critical message")
# logging.exception("An error occurred: %s", str(e))

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Function to run Flask in a separate thread
def run_flask_in_thread():
    server = make_server('127.0.0.1', 5000, app)
    print("Flask server is starting...")
    server.serve_forever()

# Function to run Telegram bot in an asyncio event loop
def run_telegram_in_loop():
    loop = asyncio.get_event_loop()  # Use the existing loop
    loop.run_until_complete(run_telegram_bot())

# Main function to run both Flask and the Telegram bot
def main():
    print("Starting both Flask and Telegram bot...")

    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask_in_thread)
    flask_thread.daemon = True  # Allow the Flask thread to exit when the main thread exits
    flask_thread.start()

    # Run the Telegram bot in the current event loop
    run_telegram_in_loop()

# Entry point
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())