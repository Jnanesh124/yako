from flask import Flask
import asyncio
from threading import Thread
from pyrogram import Client
from pyrogram.types import Message
import os  # Import to access environment variables

app = Flask(__name__)

# Your Pyrogram bot class
class Bot(Client):
    def __init__(self):
        super().__init__(
            "movie_bot",  # This serves as the session name
            bot_token=os.getenv("BOT_TOKEN"),  # Get BOT_TOKEN from environment variables
            api_id=int(os.getenv("API_ID")),  # Convert API_ID to integer
            api_hash=os.getenv("API_HASH")  # Get API_HASH from environment variables
        )

    async def on_message(self, message: Message):
        # Your bot logic goes here
        if message.text:
            await message.reply("Hello! I am your bot.")

    async def start_bot(self):
        print("Starting bot...")
        await self.start()
        print("Bot is now running!")
        await self.idle()  # Keep the bot running

# Flask route for the web server
@app.route('/')
def hello_world():
    return 'GreyMatters'

# Function to run the Pyrogram bot in a separate thread
def run_bot():
    bot = Bot()
    asyncio.run(bot.start_bot())  # Run the Pyrogram bot asynchronously

# Main entry point
if __name__ == "__main__":
    # Start the Flask web server in a separate thread
    flask_thread = Thread(target=lambda: app.run(debug=True, use_reloader=False))
    flask_thread.start()

    # Run the Pyrogram bot in the main thread (or another thread if needed)
    run_bot()
