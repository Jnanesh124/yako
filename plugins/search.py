import asyncio
from info import *
from utils import *
from time import time
from client import User
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import ChannelPrivate, PeerIdInvalid, ChannelInvalid
import difflib  # For fuzzy matching

# Auto-delete duration in seconds
AUTO_DELETE_DURATION = 60  # Adjust this value as needed

def get_best_match(query, channel_movies):
    best_match = None
    highest_score = 0
    for movie in channel_movies:
        title = movie["title"]
        try:
            levenshtein = difflib.SequenceMatcher(None, query, title).ratio()
            jaccard = len(set(query.lower().split()) & set(title.lower().split())) / max(1, len(set(query.lower().split()) | set(title.lower().split())))
            cosine = len(set(query.lower().split()) & set(title.lower().split())) / max(1, (len(query.split()) * len(title.split()))**0.5)
            phonetic = 1.0 if difflib.get_close_matches(query, [title], n=1, cutoff=0.8) else 0
            score = (levenshtein + jaccard + cosine + phonetic) / 4  
        except ZeroDivisionError:
            score = 0  

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

    # Clean query (Remove @, #, http)
    query = message.text.strip()
    query = ' '.join([word for word in query.split() if not word.startswith(('#', '@', 'www', 'http'))])

    # Display "Searching..." message
    searching_msg = await message.reply_text(f"<b>Searching:</b> <i>{query}</i>", disable_web_page_preview=True)

    head = "🎬 <b>Search Results</b> 🎬\n\n"
    results = ""
    seen_titles = set()  # Store seen titles to avoid duplicates
    msg = None  # Initialize msg to avoid reference issues

    try:
        for channel in channels:
            try:
                async for msg in User.search_messages(chat_id=channel, query=query):
                    # Delete searching message before showing results
                    await searching_msg.delete()
                    
                    name = (msg.text or msg.caption).split("\n")[0]
                    if name in seen_titles:
                        continue  # Skip duplicate titles
                    
                    best_match = get_best_match(query, [{"title": name, "link": msg.link}])
                    
                    if best_match and best_match["title"] == name:
                        results += f"🍿 <b>{best_match['title']}</b>\n🔗 <a href='{msg.link}'>📥 Download Here</a>\n\n"
                        seen_titles.add(name)  # Mark this title as seen
            except (ChannelPrivate, PeerIdInvalid, ChannelInvalid):
                print(f"Skipping invalid channel: {channel}")  
                continue  
            except Exception as e:
                print(f"Error accessing channel {channel}: {e}")
                continue

        if not results:
            await searching_msg.delete()  # Ensure searching message is deleted before showing failure
            movies = await search_imdb(query)
            if movies:
                buttons = [[InlineKeyboardButton(f"🎥 {movie['title']}", callback_data=f"recheck_{movie['id']}")] for movie in movies]
                reply_markup = InlineKeyboardMarkup(buttons)
            else:
                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("📥 Get Direct FILE Here 📥", url="https://t.me/Theater_Print_Movies_Search_bot")]])

            await message.reply_text(
                text="😔 <b>No direct links found!</b>\n\n🔍 Try searching with a different name!",
                reply_markup=reply_markup
            )
        else:
            msg = await message.reply_text(text=head + results, disable_web_page_preview=True)

        # Auto-delete after specified duration if msg exists
        if msg:
            await asyncio.sleep(AUTO_DELETE_DURATION)
            await msg.delete()

    except Exception as e:
        await searching_msg.delete()  # Ensure searching message is deleted in case of error
        print(f"An error occurred: {e}")
        await message.reply_text(f"🚨 <b>Error!</b>\n\n⚠️ Something went wrong: <code>{e}</code>\n\nPlease try again later.", disable_web_page_preview=True)

@Client.on_callback_query(filters.regex(r"^recheck"))
async def recheck(bot, update):
    clicked = update.from_user.id
    try:
        typed = update.message.reply_to_message.from_user.id
    except:
        return await update.message.delete()

    if clicked != typed:
        return await update.answer("⚠️ That's not for you! 👀", show_alert=True)

    m = await update.message.edit("🔍 <b>Rechecking the movie name...</b> ⏳")
    id = update.data.split("_")[-1]
    query = await search_imdb(id)
    channels = (await get_group(update.message.chat.id))["channels"]
    head = "<b>✅ Movie found! Here is the correct match:</b>\n\n"
    results = ""
    seen_titles = set()

    try:
        for channel in channels:
            try:
                async for msg in User.search_messages(chat_id=channel, query=query):
                    name = (msg.text or msg.caption).split("\n")[0]
                    if name in seen_titles:
                        continue
                    
                    best_match = get_best_match(query, [{"title": name, "link": msg.link}])

                    if best_match and best_match["title"] == name:
                        results += f"🍿 <b>{best_match['title']}</b>\n🔗 <a href='{msg.link}'>📥 Download Here</a>\n\n"
                        seen_titles.add(name)

            except (ChannelPrivate, PeerIdInvalid, ChannelInvalid):
                print(f"Skipping invalid channel: {channel}")  
                continue  
            except Exception as e:
                print(f"Error accessing channel {channel}: {e}")
                continue

        if not results:
            return await update.message.edit(
                "🥹 <b>Sorry, no direct download link found! ❌</b>\n\n📥 Try requesting the file from our bot below:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Get Direct FILE Here 📥", url="https://t.me/Theater_Print_Movies_Search_bot")]])
            )

        await update.message.edit(text=head + results, disable_web_page_preview=True)

        # Auto-delete after specified duration
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await update.message.delete()

    except Exception as e:
        await update.message.edit(f"🚨 <b>Error!</b>\n\n⚠️ Something went wrong: <code>{e}</code>")
        
@Client.on_callback_query(filters.regex(r"^request"))
async def request(bot, update):
    clicked = update.from_user.id
    try:
        typed = update.message.reply_to_message.from_user.id
    except:
        return await update.message.delete()

    if clicked != typed:
        return await update.answer("⚠️ That's not for you! 👀", show_alert=True)

    admin = (await get_group(update.message.chat.id))["user_id"]
    id = update.data.split("_")[1]
    name = await search_imdb(id)
    url = "https://www.imdb.com/title/tt" + id
    text = f"📢 <b>New Movie Request!</b>\n\n🎬 <b>Name:</b> {name}\n🎟️ <b>IMDb:</b> <a href='{url}'>Click Here</a>"

    msg = await bot.send_message(chat_id=admin, text=text, disable_web_page_preview=True)

    # Auto-delete after specified duration
    await asyncio.sleep(AUTO_DELETE_DURATION)
    await msg.delete()

    await update.answer("✅ <b>Request Sent to Admin!</b>", show_alert=True)
    await update.message.delete()
