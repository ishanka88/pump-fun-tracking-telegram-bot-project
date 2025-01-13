from flask import Flask, render_template
from telegram_bot.bot import run_telegram_bot
import asyncio
from config import Config

app = Flask(__name__)

# Load the configuration from the Config class
app.config.from_object(Config)

@app.route('/')
def home():
    return render_template("index.html")  # Add an HTML template for your home page

if __name__ == "__main__":
    from threading import Thread
    
    # Run Telegram bot in a separate thread
    bot_thread = Thread(target=run_telegram_bot)
    bot_thread.start()
    
    # Run the Flask app
    app.run(debug=True, use_reloader=False)  # Use reloader=False because Flask is already running in a thread
