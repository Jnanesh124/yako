import asyncio
import difflib
from time import time
from info import *
from utils import *
from client import User
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import ChannelPrivate, PeerIdInvalid, MessageNotModified, ChannelInvalid, ReplyMarkupInvalid

AUTO_DELETE_DURATION = 60  

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

    query = message.text.strip()
    query = ' '.join([word for word in query.split() if not word.startswith(('#', '@', 'http'))])

    head = "<blockquote>👀 Here are the results 👀</blockquote>\n\n"
    results = ""

    # 🔹 Show "Searching..." message & delete it instantly
    searching_msg = await message.reply_text(f"<strong>Searching: {query}</strong>", disable_web_page_preview=True)
    await asyncio.sleep(1)  # Small delay for visibility
    try:
        await searching_msg.delete()
    except Exception:
        pass  # Ignore errors if already deleted

    try:
        for channel in channels:
            try:
                async for msg in User.search_messages(chat_id=channel, query=query):
                    name = (msg.text or msg.caption).split("\n")[0]
                    best_match = get_best_match(query, [{"title": name, "link": msg.link}])

                    if best_match and best_match["title"] == name:
                        results += f"<strong>🍿 {best_match['title']}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"
                        
            except (ChannelPrivate, PeerIdInvalid, ChannelInvalid):
                print(f"Skipping invalid channel: {channel}")  
                continue  
            except Exception as e:
                print(f"Error accessing channel {channel}: {e}")
                continue  

        if not results:
            movies = await search_imdb(query)
            buttons = [[InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}")] for movie in movies]
            msg = await message.reply_text(
                "<blockquote>😔 No direct results found, but here are some IMDb suggestions 😔</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            msg = await message.reply_text(text=head + results, disable_web_page_preview=True)

        await asyncio.sleep(AUTO_DELETE_DURATION)
        await msg.delete()

    except Exception as e:
        print(f"Error in search: {e}")
        try:
            await message.reply_text(f"❌ Error occurred: {e}")
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

    try:
        await update.message.edit("Searching for IMDb movie...💥 Please wait")
    except MessageNotModified:
        pass  

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
                    best_match = get_best_match(query, [{"title": name, "link": msg.link}])

                    if best_match and best_match["title"] == name:
                        results += f"<strong>🍿 {best_match['title']}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"
                        
            except (ChannelPrivate, PeerIdInvalid, ChannelInvalid):
                print(f"Skipping invalid channel: {channel}")  
                continue  
            except Exception as e:
                print(f"Error accessing channel {channel}: {e}")
                continue  

        if not results:
            return await update.message.edit(
                "<blockquote>🥹 Sorry, no terabox link found ❌</blockquote>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Get Direct FILE Here 📥", url="https://t.me/Theater_Print_Movies_Search_bot")]]),
                disable_web_page_preview=True
            )
        
        await update.message.edit(text=head + results, disable_web_page_preview=True)

        await asyncio.sleep(AUTO_DELETE_DURATION)
        await update.message.delete()

    except Exception as e:
        print(f"Error in recheck: {e}")
