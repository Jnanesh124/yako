import asyncio
from info import *
from utils import *
from time import time
from client import User
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import ChannelPrivate, PeerIdInvalid
import difflib  # For fuzzy matching

# Auto-delete duration in seconds
AUTO_DELETE_DURATION = 60  # Adjust this value as needed

def token_match(query, movie_name):
    """
    Token-based fuzzy matching function. Breaks both the query and movie title into tokens and compares them using fuzzy matching.
    """
    # Tokenize the query and movie title by splitting by spaces
    query_tokens = query.lower().split()
    movie_tokens = movie_name.lower().split()

    # Compare tokens using difflib's SequenceMatcher for fuzzy matching
    matched_tokens = 0
    for token in query_tokens:
        # Check for similarity with each token in the movie name
        for movie_token in movie_tokens:
            similarity = difflib.SequenceMatcher(None, token, movie_token).ratio()
            if similarity > 0.7:  # You can adjust this threshold for more or less strict matching
                matched_tokens += 1
                break  # Stop after finding one matching token

    # If a sufficient number of tokens match, return True
    return matched_tokens >= len(query_tokens) // 2  # Match at least half of the tokens

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

    query = message.text.strip()
    
    # Remove unwanted characters like hashtags, @ mentions, and links
    query = ' '.join([word for word in query.split() if not word.startswith(('#', '@', 'http'))])

    head = "<blockquote>👀 Here are the results 👀</blockquote>\n\n"
    results = ""

    # Display "Searching..." message with query information
    msg = await message.reply_text(f"Searching for '{query}'...💥 Please wait", disable_web_page_preview=True)

    try:
        for channel in channels:
            # Check if the bot can access the channel, handle potential errors
            try:
                async for msg in User.search_messages(chat_id=channel, query=query):
                    name = (msg.text or msg.caption).split("\n")[0]

                    # Use token-based fuzzy matching here
                    if token_match(query, name):
                        if name in results:
                            continue
                        results += f"<strong>🍿 {name}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"
            except (ChannelPrivate, PeerIdInvalid) as e:
                print(f"Channel {channel} is inaccessible or banned, skipping...")
                continue  # Skip this channel if it’s private or invalid
            except Exception as e:
                print(f"Error accessing channel {channel}: {e}")
                continue  # Skip this channel on any other error

        # Remove "Searching..." message
        await msg.delete()

        if not results:
            movies = await search_imdb(query)
            buttons = [[InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}")] for movie in movies]
            msg = await message.reply_text(
                text="<blockquote>😔 No direct results found for your search, but I found some IMDb suggestions 😔</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            msg = await message.reply_text(text=head + results, disable_web_page_preview=True)

        # Auto-delete the message after the specified duration
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await msg.delete()

    except Exception as e:
        print(f"Error in search: {e}")  # Log the error for debugging
        await msg.edit(f"❌ Error occurred: {e}")
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await msg.delete()

@Client.on_callback_query(filters.regex(r"^recheck"))
async def recheck(bot, update):
    clicked = update.from_user.id
    try:
        typed = update.message.reply_to_message.from_user.id
    except:
        return await update.message.delete()

    if clicked != typed:
        return await update.answer("That's not for you! 👀", show_alert=True)

    # Display "Searching..." message with query information
    m = await update.message.edit(f"Searching for IMDb movie...💥 Please wait")

    id = update.data.split("_")[-1]
    query = await search_imdb(id)
    channels = (await get_group(update.message.chat.id))["channels"]
    head = "<b>👇 I Have Searched Movie With Wrong Spelling But Take care next time 👇</b>\n\n"
    results = ""

    try:
        for channel in channels:
            # Check if the bot can access the channel, handle potential errors
            try:
                async for msg in User.search_messages(chat_id=channel, query=query):
                    name = (msg.text or msg.caption).split("\n")[0]

                    # Use token-based fuzzy matching here
                    if token_match(query, name):
                        if name in results:
                            continue
                        results += f"<strong>🍿 {name}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"
            except (ChannelPrivate, PeerIdInvalid) as e:
                print(f"Channel {channel} is inaccessible or banned, skipping...")
                continue  # Skip this channel if it’s private or invalid
            except Exception as e:
                print(f"Error accessing channel {channel}: {e}")
                continue  # Skip this channel on any other error

        # Remove "Searching..." message
        await m.delete()

        if not results:
            return await update.message.edit(
                "<blockquote>🥹 Sorry, no terabox link found ❌\n\nRequest Below 👇 Bot To Get Direct FILE📥</blockquote>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Get Direct FILE Here 📥", url="https://t.me/Theater_Print_Movies_Search_bot")]]),
                disable_web_page_preview=True
            )
        await update.message.edit(text=head + results, disable_web_page_preview=True)

        # Auto-delete the message after the specified duration
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await update.message.delete()

    except Exception as e:
        await update.message.edit(f"❌ Error: {e}")
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await update.message.delete()
