import asyncio
from info import *
from utils import *
from time import time
from client import User
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from fuzzywuzzy import fuzz, process
import re

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

    # Send a live search message
    live_msg = await message.reply_text(f"Searching for '{query}'...")

    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption or "").split("\n")[0]
                if name in results:
                    continue
                if fuzz.partial_ratio(query.lower(), name.lower()) > 70:
                    results += f"<strong>🍿 {name}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"

        if not results:
            # Use IMDb spelling check when no results are found in channels
            movies = await search_imdb(query)
            if movies:
                buttons = [[InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}")] for movie in movies]
                await live_msg.edit_text(
                    text="<blockquote>😔 No exact match found. Did you mean one of these?</blockquote>",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            else:
                await live_msg.edit_text(
                    text="<blockquote>😔 No results found on IMDb either. Please try again.</blockquote>"
                )
        else:
            await live_msg.edit_text(text=head + results, disable_web_page_preview=True)

        # Auto-delete the message after the specified duration
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await live_msg.delete()

    except Exception as e:
        print(f"Error in search: {e}")  # Log the error for debugging
        await live_msg.edit_text(f"❌ An error occurred: {e}")

@Client.on_callback_query(filters.regex(r"^recheck"))
async def recheck(bot, update):
    user_id = update.from_user.id
    try:
        typed_user_id = update.message.reply_to_message.from_user.id
    except AttributeError:
        return await update.message.delete()

    if user_id != typed_user_id:
        return await update.answer("That's not for you! 👀", show_alert=True)

    movie_id = update.data.split("_")[-1]
    query = await search_imdb(movie_id)  # Fetch the movie name using its IMDb ID
    channels = (await get_group(update.message.chat.id))["channels"]
    results = ""
    head = "<b>👇 Results for your corrected search 👇</b>\n\n"

    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption or "").split("\n")[0]
                if name in results:
                    continue
                if fuzz.token_set_ratio(query.lower(), name.lower()) > 70:
                    results += f"<strong>🍿 {name}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"

        if not results:
            await update.message.edit_text(
                text="<blockquote>🥹 Sorry, no results found. Please try another query.</blockquote>"
            )
        else:
            await update.message.edit_text(text=head + results, disable_web_page_preview=True)

        # Auto-delete the message after the specified duration
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await update.message.delete()

    except Exception as e:
        await update.message.edit_text(f"❌ Error: {e}")

async def search_imdb(query):
    """
    Searches IMDb and returns a list of unique movies matching the query.
    """
    query = re.sub(r"\s+", " ", query.strip().lower())  # Normalize query
    # Mock IMDb search results (replace with your actual IMDb search logic)
    results = [
        {"id": "tt1234567", "title": "K.G.F: Chapter 2"},
        {"id": "tt7654321", "title": "K.G.F: Chapter 1"},
        {"id": "tt2233445", "title": "K.G.F: Chapter 2"}  # Duplicate title example
    ]
    matches = process.extract(query, [movie["title"] for movie in results], scorer=fuzz.token_set_ratio, limit=5)
    unique_titles = set()
    filtered_results = []
    for movie_title, score, idx in matches:
        if score >= 70 and results[idx]["title"] not in unique_titles:
            unique_titles.add(results[idx]["title"])
            filtered_results.append({"id": results[idx]["id"], "title": results[idx]["title"]})
    return filtered_results
