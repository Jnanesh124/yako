from pyrogram import Client
import asyncio

print("Bot Started 👍")

# Ensure the Bot class inherits from pyrogram.Client
class Bot(Client):
    def __init__(self):
        super().__init__(
            "my_bot",  # Session name
            api_id="29942004",  # Your API ID from https://my.telegram.org
            api_hash="ad92f01e4a90cddebbea0ad16fa23026",  # Your API Hash
            bot_token="6765313019:AAHYLXnKN_q5dhznb-4IuLddejkCFleIUg8"  # Your bot token from BotFather
        )

    # Optionally, add other methods to handle specific bot functionality

# Create an instance of your Bot class
bot = Bot()

# Using asyncio to start the bot and keep it running
async def run_bot():
    await bot.start()  # Start the bot
    print("Bot is running!")  # Confirmation that bot is running
    await bot.idle()  # Keep the bot running until manually stopped

# Run the bot
asyncio.run(run_bot())  # This will start the bot and keep it running
