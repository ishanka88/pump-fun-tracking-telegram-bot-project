from flask import Flask, render_template
from telegram_bot.bot import run_telegram_bot
import asyncio
from config import Config
import threading
import time
from telegram_bot.methods import get_current_sol_value


app = Flask(__name__)

# Load the configuration from the Config class
app.config.from_object(Config)

@app.route('/')
def home():
    return render_template("index.html")  # Add an HTML template for your home page



# Method to be executed periodically
def sol_value():
   Config.CURRENT_SOL_VALUE =get_current_sol_value() 

# Function to run sol_value every 2 minutes
def run_periodically():
    while True:
        sol_value()
        time.sleep(120)  # Wait for 2 minutes

if __name__ == "__main__":
    from threading import Thread
    
    # Run Telegram bot in a separate thread
    bot_thread = Thread(target=run_telegram_bot)
    bot_thread.start()
    
    # Run the Flask app
    app.run(debug=True, use_reloader=False)  # Use reloader=False because Flask is already running in a thread

    def sol_value():
        print("Method executed!")

    def run_periodically():
        while True:
            sol_value()
            time.sleep(120)  # Wait for 2 minutes

    # Create a new thread to run sol_value periodically
    period_thread = Thread(target=run_periodically)
    period_thread.daemon = True  # This ensures the thread will exit when the main program exits
    period_thread.start()
