import asyncio
from info import *
from utils import *
from time import time
from client import User
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Auto-delete duration in seconds
AUTO_DELETE_DURATION = 60  # Adjust this value as needed


@Client.on_message(filters.text & filters.group & filters.incoming & ~filters.command(["verify", "connect", "id"]))
async def search(bot, message):
    f_sub = await force_sub(bot, message)
    if not f_sub:
        return
    channels = (await get_group(message.chat.id))["channels"]
    if not channels:
        return
    if message.text.startswith("/"):
        return

    query = message.text
    head = "<blockquote>👀 Here are the results 👀</blockquote>\n\n"
    results = ""

    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                results += f"<strong>🍿 {name}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"

        if not results:
            movies = await search_imdb(query)
            buttons = [[InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}")] for movie in movies]
            msg = await message.reply_text(
                text="<blockquote>😔 Only Type Movie Name 😔</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            msg = await message.reply_text(text=head + results, disable_web_page_preview=True)

        # Auto-delete the message after the specified duration
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await msg.delete()

    except Exception as e:
        print(f"Error in search: {e}")  # Log the error for debugging


@Client.on_message(filters.text & filters.private & filters.incoming)
async def pm_search(bot, message):
    # Public channel usernames
    channels = ["@JN2FLIX_KANNADA", "JN2FLIX_TELUGU"]  # Replace with actual public channel usernames

    query = message.text
    head = "<blockquote>👀 Here are the results 👀</blockquote>\n\n"
    results = ""

    try:
        for channel in channels:
            # Use the bot client to search in public channels
            async for msg in bot.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                results += f"<strong>🍿 {name}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"

        if not results:
            return await message.reply_text(
                "<blockquote>😔 Sorry, no results found. Please check the movie name and try again. 😔</blockquote>"
            )

        # Send the search results back to the user
        await message.reply_text(text=head + results, disable_web_page_preview=True)

    except Exception as e:
        print(f"Error in PM search: {e}")
        await message.reply_text("❌ An error occurred while processing your request. Please try again later.")
