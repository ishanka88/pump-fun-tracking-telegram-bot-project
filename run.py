import asyncio
import threading
import nest_asyncio
from website import app  # Flask app
from telegram_bot.bot import run_telegram_bot  # Your Telegram bot logic
from werkzeug.serving import make_server

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