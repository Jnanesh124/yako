import asyncio
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import *
from utils import *
from time import time
from client import User

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
            try:
                async for msg in User.search_messages(chat_id=channel, query=query):
                    # Log the channel name and ID for debugging
                    print(f"Searching in channel: {channel} (ID: {channel})")

                    # Ensure that msg.text or msg.caption is not None before processing
                    text = msg.text or msg.caption or ""
                    name = text.split("\n")[0]

                    # Ensure `name` is not empty and contains valid data
                    if not name:
                        continue

                    # Use fuzzy matching to find similar results (allow for variations like year, language)
                    if fuzz.partial_ratio(query.lower(), name.lower()) > 70:
                        results += f"<strong>🍿 {name}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"
            
            except Exception as e:
                # Log and skip inaccessible channels
                print(f"Skipping channel {channel}: {e}")
                continue

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
    clicked = update.from_user.id
    try:
        typed = update.message.reply_to_message.from_user.id
    except:
        return await update.message.delete()       

    if clicked != typed:
        return await update.answer("That's not for you! 👀", show_alert=True)

    m = await update.message.edit("Searching..💥")
    id = update.data.split("_")[-1]
    query = await search_imdb(id)
    channels = (await get_group(update.message.chat.id))["channels"]
    head = "<b>👇 I Have Searched Movie With Wrong Spelling But Take care next time 👇</b>\n\n"
    results = ""

    try:
        for channel in channels:
            try:
                async for msg in User.search_messages(chat_id=channel, query=query):
                    # Ensure that msg.text or msg.caption is not None before processing
                    text = msg.text or msg.caption or ""
                    name = text.split("\n")[0]

                    # Ensure `name` is not empty and contains valid data
                    if not name:
                        continue
                    
                    # Use fuzzy matching to find similar results (allow for variations like year, language)
                    if fuzz.partial_ratio(query.lower(), name.lower()) > 70:
                        results += f"<strong>🍿 {name}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"
            
            except Exception as e:
                # Log and skip inaccessible channels
                print(f"Skipping channel {channel}: {e}")
                continue

        if not results:
            return await update.message.edit(
                "<blockquote>🥹 Sorry, no terabox link found ❌\n\nRequest Below 👇  Bot To Get Direct FILE📥</blockquote>", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Get Direct FILE Here 📥", url="https://t.me/Theater_Print_Movies_Search_bot")]])
            )
        
        await update.message.edit(text=head + results, disable_web_page_preview=True)

        # Auto-delete the message after the specified duration
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await update.message.delete()

    except Exception as e:
        await update.message.edit(f"❌ Error: {e}")


@Client.on_callback_query(filters.regex(r"^request"))
async def request(bot, update):
    clicked = update.from_user.id
    try:
        typed = update.message.reply_to_message.from_user.id
    except:
        return await update.message.delete()       

    if clicked != typed:
        return await update.answer("That's not for you! 👀", show_alert=True)

    admin = (await get_group(update.message.chat.id))["user_id"]
    id = update.data.split("_")[1]
    name = await search_imdb(id)
    url = "https://www.imdb.com/title/tt" + id
    text = f"#RequestFromYourGroup\n\nName: {name}\nIMDb: {url}"
    
    msg = await bot.send_message(chat_id=admin, text=text, disable_web_page_preview=True)

    # Auto-delete the message after the specified duration
    await asyncio.sleep(AUTO_DELETE_DURATION)
    await msg.delete()

    await update.answer("✅ Request Sent To Admin", show_alert=True)
    await update.message.delete()


async def search_imdb(query):
    """Search IMDb for a movie or series based on a query."""
    try:
        movies = []
        # Use a more refined query search, removing extra words like 'language' or 'year'
        cleaned_query = ' '.join([word for word in query.split() if word.lower() not in ['kannada', 'tamil', 'year', '2019', '2024']])

        # Assuming a function `imdb_search` exists that returns results in a suitable format
        search_results = await imdb_search(cleaned_query)
        
        for result in search_results:
            # Return top 3 results from IMDb (adjust according to your logic)
            movies.append({
                'id': result['id'],
                'title': result['title']
            })

        return movies
    except Exception as e:
        print(f"Error in IMDb search: {e}")
        return []
