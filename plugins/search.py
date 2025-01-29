import asyncio
from info import *
from utils import *
from time import time
from client import User
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import ChannelPrivate, PeerIdInvalid
import difflib  # For fuzzy matching

AUTO_DELETE_DURATION = 60  # Auto-delete messages after 60 seconds
MAX_BUTTON_TEXT_LENGTH = 64  # Telegram's max button text length
STORAGE_CHANNEL = -1002051432955  # Define your storage channel using channel ID

def token_match(query, movie_name):
    query_tokens = query.lower().split()
    movie_tokens = movie_name.lower().split()

    matched_tokens = 0
    for token in query_tokens:
        for movie_token in movie_tokens:
            similarity = difflib.SequenceMatcher(None, token, movie_token).ratio()
            if similarity > 0.7:
                matched_tokens += 1
                break

    return matched_tokens >= len(query_tokens) // 2

def format_title_for_button(title):
    """Format long movie titles so they fit properly in a single button."""
    if len(title) <= MAX_BUTTON_TEXT_LENGTH:
        return title  # No need to modify if it's short enough
    
    words = title.split()  # Split title into words
    new_title = ""
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > MAX_BUTTON_TEXT_LENGTH:  
            new_title += "\n"  # Add a line break before exceeding 64 chars
            current_length = 0  
        new_title += word + " "  
        current_length += len(word) + 1  
    
    return new_title.strip()  # Remove extra spaces

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
    buttons = []

    try:
        for channel in channels:
            try:
                async for msg in User.search_messages(chat_id=channel, query=query):
                    name = (msg.text or msg.caption).split("\n")[0]

                    if token_match(query, name):
                        if any(name in btn[0].text for btn in buttons):
                            continue

                        formatted_title = format_title_for_button(name)
                        buttons.append([InlineKeyboardButton(f"🍿 {formatted_title}", url=msg.link)])

            except (ChannelPrivate, PeerIdInvalid):
                continue
            except Exception as e:
                print(f"Error accessing channel {channel}: {e}")
                continue

        if not buttons:
            movies = await search_imdb(query)
            buttons = [[InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}")] for movie in movies]
            msg = await message.reply_text(
                text="<blockquote>😔 Only Type Movie Name 😔</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            msg = await message.reply_text(
                text=head,
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        await asyncio.sleep(AUTO_DELETE_DURATION)
        await msg.delete()

    except Exception as e:
        print(f"Error in search: {e}")

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
    buttons = []

    try:
        for channel in channels:
            try:
                async for msg in User.search_messages(chat_id=channel, query=query):
                    name = (msg.text or msg.caption).split("\n")[0]

                    if token_match(query, name):
                        if any(name in btn[0].text for btn in buttons):
                            continue

                        formatted_title = format_title_for_button(name)
                        buttons.append([InlineKeyboardButton(f"🍿 {formatted_title}", url=msg.link)])

            except (ChannelPrivate, PeerIdInvalid):
                continue
            except Exception as e:
                print(f"Error accessing channel {channel}: {e}")
                continue

        if not buttons:
            return await update.message.edit(
                "<blockquote>🥹 Sorry, no terabox link found ❌\n\nRequest Below 👇  Bot To Get Direct FILE📥</blockquote>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Get Direct FILE Here 📥", url="https://t.me/Theater_Print_Movies_Search_bot")]])
            )
        await update.message.edit(text=head, reply_markup=InlineKeyboardMarkup(buttons))

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

    await asyncio.sleep(AUTO_DELETE_DURATION)
    await msg.delete()

    await update.answer("✅ Request Sent To Admin", show_alert=True)
    await update.message.delete()

# New feature to store and forward file links
@Client.on_message(filters.document & filters.group)
async def store_file(bot, message):
    try:
        # Check if message is a file and store it
        file = message.document
        if file:
            # Use channel ID for the storage channel
            storage_channel = -1001234567890  # Channel ID
            file_link = await bot.get_file(file.file_id)

            # Forward the file to the storage channel
            stored_message = await bot.send_document(
                storage_channel,  # Numeric channel ID
                file_link.file_url,
                caption=f"📥 File stored: {file.file_name}",
            )

            # Send the generated storage link back to the user
            storage_link = f"https://t.me/{bot.username}?start={stored_message.message_id}"
            await message.reply(f"✅ File has been stored! You can access it here: {storage_link}")

    except Exception as e:
        print(f"Error storing file: {e}")
        await message.reply("❌ Failed to store file.")
