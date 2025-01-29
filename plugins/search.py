import asyncio
import base64
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
STORAGE_CHANNEL = "@JN2FLIX_KANNADA"  # Your storage channel
BOT_USERNAME = "Rockers_Postsearch_Bot"  # Replace with your bot's username

def token_match(query, movie_name):
    query_tokens = query.lower().split()
    movie_tokens = movie_name.lower().split()

    matched_tokens = sum(
        any(difflib.SequenceMatcher(None, token, movie_token).ratio() > 0.7 for movie_token in movie_tokens)
        for token in query_tokens
    )
    
    return matched_tokens >= len(query_tokens) // 2

def format_title_for_button(title):
    """Ensure the movie title fits within the Telegram button character limit."""
    return title if len(title) <= MAX_BUTTON_TEXT_LENGTH else title[:MAX_BUTTON_TEXT_LENGTH - 3] + "..."

def encode_data(data):
    """Encode data to base64."""
    return base64.urlsafe_b64encode(data.encode()).decode()

def decode_data(data):
    """Decode data from base64."""
    return base64.urlsafe_b64decode(data.encode()).decode()

@Client.on_message(filters.text & filters.group & filters.incoming & ~filters.command(["verify", "connect", "id"]))
async def search(bot, message):
    f_sub = await force_sub(bot, message)
    if not f_sub:
        return

    query = message.text
    head = "<blockquote>👀 Here are the results 👀</blockquote>\n\n"
    buttons = []

    try:
        async for msg in bot.search_messages(STORAGE_CHANNEL, query):
            name = (msg.text or msg.caption).split("\n")[0]
            if token_match(query, name) and not any(name in btn[0].text for btn in buttons):
                encoded_data = encode_data(f"get-{msg.message_id}")
                link = f"https://t.me/{BOT_USERNAME}?start={encoded_data}"
                buttons.append([InlineKeyboardButton(f"🍿 {format_title_for_button(name)}", url=link)])

        if not buttons:
            msg = await message.reply_text(
                text="<blockquote>😔 No files found 😔</blockquote>",
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

@Client.on_message(filters.command("start") & filters.private)
async def start(bot, message):
    if len(message.command) > 1:
        try:
            data = decode_data(message.command[1])
            if data.startswith("get-"):
                message_id = int(data.split("-")[1])
                await bot.forward_messages(
                    chat_id=message.chat.id,
                    from_chat_id=STORAGE_CHANNEL,
                    message_ids=message_id
                )
        except Exception as e:
            print(f"Error decoding start parameter: {e}")
            await message.reply("❌ Failed to retrieve the file.")
    else:
        await message.reply("Welcome! Use this bot to search and retrieve files.")

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

@Client.on_message(filters.document & filters.group)
async def store_file(bot, message):
    try:
        file = message.document
        if not file:
            return
        
        file_name = file.file_name
        file_caption = f"📥 File stored: {file_name}"

        # Check if file already exists
        async for msg in bot.search_messages(STORAGE_CHANNEL, file_name):
            if msg.document:
                storage_link = f"https://t.me/{BOT_USERNAME}?start={encode_data(f'get-{msg.message_id}')}"
                await message.reply(f"✅ File already exists! You can access it here: {storage_link}")
                return  # Stop execution

        # If file is not found, store it
        stored_message = await bot.copy_message(
            chat_id=STORAGE_CHANNEL,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )

        # Generate and send the storage link
        storage_link = f"https://t.me/{BOT_USERNAME}?start={encode_data(f'get-{stored_message.message_id}')}"
        await message.reply(f"✅ File has been stored! You can access it here: {storage_link}")

    except Exception as e:
        print(f"Error storing file: {e}")
        await message.reply("❌ Failed to store file.")
