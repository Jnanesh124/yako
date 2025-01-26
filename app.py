from flask import Flask
import asyncio
from threading import Thread
from pyrogram import Client
from pyrogram.types import Message

app = Flask(__name__)

# Your Pyrogram bot class
class Bot(Client):
    def __init__(self):
        super().__init__(
            "movie_bot",
            bot_token="YOUR_BOT_TOKEN",
            api_id="YOUR_API_ID",
            api_hash="YOUR_API_HASH",
            session_name="YOUR_SESSION_NAME"
        )

    async def on_message(self, message: Message):
        # Your bot logic goes here
        if message.text:
            await message.reply("Hello! I am your bot.")

    async def start_bot(self):
        await self.start()

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
