import asyncio
from difflib import get_close_matches
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

        # Fuzzy search in case no exact matches are found
        if not results:
            messages = []
            for channel in channels:
                async for msg in User.search_messages(chat_id=channel, query=""):  # Retrieve all messages
                    messages.append(msg)

            close_matches = get_fuzzy_matches(query, messages)
            if close_matches:
                results = format_fuzzy_results(close_matches)

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
    live_msg = None

    try:
        # Acknowledge the user's query with a "Searching..." message
        live_msg = await message.reply_text("<blockquote>🔍 Searching for your query...</blockquote>")
        
        # Delete the user's query message
        await message.delete()

        head = "<blockquote>👀 Here are the results 👀</blockquote>\n\n"
        results = ""

        # Perform the search in the specified channels
        for channel in channels:
            async for msg in bot.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                results += f"<strong>🍿 {name}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"

        # Fuzzy search in case no exact matches are found
        if not results:
            messages = []
            for channel in channels:
                async for msg in bot.search_messages(chat_id=channel, query=""):  # Retrieve all messages
                    messages.append(msg)

            close_matches = get_fuzzy_matches(query, messages)
            if close_matches:
                results = format_fuzzy_results(close_matches)

        # If still no results, show a no-results message
        if not results:
            results = "<blockquote>😔 Sorry, no results found. Please check the movie/season name and try again. 😔</blockquote>"

        # Replace the "Searching..." message with the results
        await live_msg.edit_text(text=head + results, disable_web_page_preview=True)

        # Auto-delete the results message after a specified duration
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await live_msg.delete()

    except Exception as e:
        print(f"Error in PM search: {e}")
        if live_msg:
            await live_msg.edit_text("❌ An error occurred while processing your request. Please try again later.")

        # Auto-delete error message after a specified duration
        await asyncio.sleep(AUTO_DELETE_DURATION)
        if live_msg:
            await live_msg.delete()


def get_fuzzy_matches(query, messages, threshold=0.6):
    """
    Finds fuzzy matches for the query in a list of messages.
    :param query: The search query.
    :param messages: A list of messages to search in.
    :param threshold: The minimum similarity ratio for matches (default is 0.6).
    :return: A list of matching messages.
    """
    matches = []
    for msg in messages:
        name = (msg.text or msg.caption or "").split("\n")[0]
        if name and get_close_matches(query, [name], cutoff=threshold):
            matches.append(msg)
    return matches


def format_fuzzy_results(matches):
    """
    Formats fuzzy search results.
    :param matches: A list of matching messages.
    :return: A formatted string of results.
    """
    results = ""
    for msg in matches:
        name = (msg.text or msg.caption).split("\n")[0]
        results += f"<strong>🍿 {name}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"
    return results
