from client import Bot  # Assuming Bot is your class that inherits from pyrogram.Client

print("Bot Started 👍")

# Create an instance of your Bot class
bot = Bot()

# Start the bot using asyncio
import asyncio

# Using asyncio to start the bot and keep it running
async def run_bot():
    await bot.start()  # Start the bot
    print("Bot is running!")  # Confirmation that bot is running
    await bot.idle()  # Keep the bot running until manually stopped

# Run the bot
asyncio.run(run_bot())  # This will start the bot and keep it running
