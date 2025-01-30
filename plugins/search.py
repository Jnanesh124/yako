import asyncio
import re
import difflib
from info import *
from utils import *
from time import time
from client import User
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import ChannelPrivate, PeerIdInvalid

# Auto-delete duration in seconds
AUTO_DELETE_DURATION = 60  # Adjust as needed

# Stopwords, languages, and formats to remove
STOPWORDS = {
    "movie", "dubbed", "download", "full", "hd", "version", "watch", "online", 
    "free", "latest", "best", "bluray", "web", "rip", "cam", "quality", "official",
    "print", "leaked", "real", "fast", "stream", "ultra", "high", "low", "super"
}
LANGUAGES = {"hindi", "english", "tamil", "telugu", "kannada", "malayalam", "bengali", "urdu"}
FORMATS = {"1080p", "720p", "480p", "360p", "hdrip", "dvdrip", "webrip", "hevc", "x264", "x265"}

# Predefined movie list for fuzzy matching
MOVIE_LIST = ["kgf", "jawan", "pushpa", "spider man", "pani", "animal", "leo", "avengers", "thor", "oppenheimer"]  # Add more

def extract_movie_name(query):
    """
    Extracts and corrects the movie name from a messy user query.
    """
    words = query.split()

    # Remove numbers (years, resolutions)
    cleaned_words = [word for word in words if not re.match(r'^\d{2,4}$', word)]

    # Remove stopwords, languages, and formats
    cleaned_words = [word for word in cleaned_words if word.lower() not in STOPWORDS]
    cleaned_words = [word for word in cleaned_words if word.lower() not in LANGUAGES]
    cleaned_words = [word for word in cleaned_words if word.lower() not in FORMATS]

    if not cleaned_words:
        return query  # If nothing is left, return original query

    cleaned_query = " ".join(cleaned_words)

    # Fuzzy match with known movies
    best_match = difflib.get_close_matches(cleaned_query, MOVIE_LIST, n=1, cutoff=0.5)

    return best_match[0] if best_match else cleaned_query

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

    # Extract and correct movie name
    extracted_movie_name = extract_movie_name(query)

    # Show real-time fuzzy correction suggestion
    correction_msg = await message.reply_text(f"🔍 Did you mean: <b>{extracted_movie_name}</b>?", disable_web_page_preview=True)
    await asyncio.sleep(2)
    await correction_msg.delete()

    head = "<blockquote>👀 Here are the results 👀</blockquote>\n\n"
    results = ""

    # Display "Searching..." message
    searching_msg = await message.reply_text(f"<strong>Searching: {extracted_movie_name}</strong>", disable_web_page_preview=True)

    try:
        for channel in channels:
            try:
                async for msg in User.search_messages(chat_id=channel, query=extracted_movie_name):
                    title = (msg.text or msg.caption).split("\n")[0]

                    if extracted_movie_name.lower() in title.lower():
                        results += f"<strong>🍿 {title}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"
            except (ChannelPrivate, PeerIdInvalid):
                continue  
            except Exception as e:
                print(f"Error accessing channel {channel}: {e}")
                continue  

        # Ensure searching message is deleted before continuing
        try:
            await searching_msg.delete()
        except Exception:
            pass  

        if not results:
            movies = await search_imdb(extracted_movie_name)
            buttons = [[InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}")] for movie in movies]
            msg = await message.reply_text(
                text="<blockquote>😔 No direct results found for your search, but I found some IMDb suggestions 😔</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            msg = await message.reply_text(text=head + results, disable_web_page_preview=True)

        # Auto-delete message after specified duration
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await msg.delete()

    except Exception as e:
        print(f"Error in search: {e}")
        try:
            await searching_msg.edit(f"❌ Error occurred: {e}")
            await asyncio.sleep(AUTO_DELETE_DURATION)
            await searching_msg.delete()
        except Exception:
            pass  
