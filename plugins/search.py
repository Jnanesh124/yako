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

# Function to perform token-based matching (based on query and movie title)
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
                matched_tokens += 2
                break  # Stop after finding one matching token

    # If a sufficient number of tokens match, return True
    return matched_tokens >= len(query_tokens) // 2  # Match at least half of the tokens

# Function to calculate best match using all 5 matching mechanisms
def get_best_match(query, channel_movies):
    best_match = None
    highest_score = 0
    for movie in channel_movies:
        title = movie["title"]
        # Perform matching for each mechanism
        levenshtein = difflib.SequenceMatcher(None, query, title).ratio()
        jaccard = len(set(query.lower().split()) & set(title.lower().split())) / len(set(query.lower().split()) | set(title.lower().split()))
        cosine = len(set(query.lower().split()) & set(title.lower().split())) / (len(query.split()) * len(title.split()))**0.5
        phonetic = 1.0 if difflib.get_close_matches(query, [title], n=1, cutoff=0.8) else 0
        token = token_match(query, title)  # Adding the token-based matching

        # Sum up the scores and find the best match
        score = (levenshtein + jaccard + cosine + phonetic + token) / 5  # Now includes token match

        if score > highest_score:
            highest_score = score
            best_match = movie

    return best_match

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

    # Display "Searching..." message
    searching_msg = await message.reply_text(f"<strong>Searching: {query}</strong>", disable_web_page_preview=True)

    # Delete the searching message immediately to indicate the process has started
    try:
        await searching_msg.delete()
    except Exception:
        pass

    try:
        # Perform the movie search across channels
        for channel in channels:
            try:
                async for msg in User.search_messages(chat_id=channel, query=query):
                    name = (msg.text or msg.caption).split("\n")[0]

                    # Get the best match for the query and movie titles in the channel
                    best_match = get_best_match(query, [{"title": name, "link": msg.link}])

                    if best_match and best_match["title"] == name:
                        results += f"<strong>🍿 {best_match['title']}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"
                        
            except (ChannelPrivate, PeerIdInvalid):
                continue  
            except Exception as e:
                print(f"Error accessing channel {channel}: {e}")
                continue  

        # If no results were found directly, try IMDb search
        if not results:
            # Search IMDb for suggestions
            movies = await search_imdb(query)
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
            await message.edit(f"❌ Error occurred: {e}")
            await asyncio.sleep(AUTO_DELETE_DURATION)
            await message.delete()
        except Exception:
            pass


@Client.on_callback_query(filters.regex(r"^recheck"))
async def recheck(bot, update):
    clicked = update.from_user.id
    try:
        typed = update.message.reply_to_message.from_user.id
    except:
        return await update.message.delete()

    if clicked != typed:
        return await update.answer("That's not for you! 👀", show_alert=True)

    # Display "Searching..." message
    searching_msg = await update.message.edit("Searching for IMDb movie...💥 Please wait")

    id = update.data.split("_")[-1]
    query = await search_imdb(id)
    channels = (await get_group(update.message.chat.id))["channels"]
    head = "<b>👇 I Have Searched Movie With Wrong Spelling But Take care next time 👇</b>\n\n"
    results = ""

    try:
        for channel in channels:
            try:
                async for msg in User.search_messages(chat_id=channel, query=query):
                    name = (msg.text or msg.caption).split("\n")[0]

                    # Get the best match for the query and movie titles in the channel
                    best_match = get_best_match(query, [{"title": name, "link": msg.link}])

                    if best_match and best_match["title"] == name:
                        results += f"<strong>🍿 {best_match['title']}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"
                        
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
            return await update.message.edit(
                "<blockquote>🥹 Sorry, no terabox link found ❌\n\nRequest Below 👇 Bot To Get Direct FILE📥</blockquote>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Get Direct FILE Here 📥", url="https://t.me/Theater_Print_Movies_Search_bot")]]),
                disable_web_page_preview=True
            )
        
        await update.message.edit(text=head + results, disable_web_page_preview=True)

        # Auto-delete message after specified duration
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await update.message.delete()

    except Exception as e:
        try:
            await update.message.edit(f"❌ Error: {e}")
            await asyncio.sleep(AUTO_DELETE_DURATION)
            await update.message.delete()
        except Exception:
            pass
