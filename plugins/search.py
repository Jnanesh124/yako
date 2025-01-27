import asyncio
from info import *
from utils import *
from time import time
from client import User
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from fuzzywuzzy import fuzz

# Auto-delete duration in seconds
AUTO_DELETE_DURATION = 60  # Adjust this value as needed

@Client.on_message(filters.text & filters.group & filters.incoming & ~filters.command(["verify", "connect", "id"]))
async def search(bot, message):
    f_sub = await force_sub(bot, message)
    if not f_sub:
        return

    # Get linked channels
    channels = (await get_group(message.chat.id))["channels"]
    if not channels:
        await message.reply_text("No channels are configured for this group.")
        return

    query = message.text
    head = "<blockquote>👀 Here are the results 👀</blockquote>\n\n"
    results = ""

    # Send a live search message
    live_msg = await message.reply_text(f"Searching for '{query}'...")

    try:
        for channel in channels:
            try:
                # Validate channel access
                chat = await bot.get_chat(channel)
                print(f"Accessing channel: {chat.title} ({chat.id})")

                # Search messages in the channel
                async for msg in User.search_messages(chat_id=channel, query=query):
                    name = (msg.text or msg.caption or "").split("\n")[0]
                    if name in results:
                        continue
                    # Use fuzzy matching for better accuracy
                    if fuzz.partial_ratio(query.lower(), name.lower()) > 80:
                        results += f"<strong>🍿 {name}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"
            except Exception as e:
                print(f"Error accessing channel {channel}: {e}")
                continue

        # Handle cases with no results
        if not results:
            await live_msg.edit_text("<blockquote>😔 No results found. Please try again.</blockquote>")
        else:
            await live_msg.edit_text(text=head + results, disable_web_page_preview=True)

        # Auto-delete after specified duration
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await live_msg.delete()

    except Exception as e:
        print(f"Error in search: {e}")
        await live_msg.edit_text(f"An error occurred: {e}")


@Client.on_callback_query(filters.regex(r"^recheck"))
async def recheck(bot, update):
    clicked = update.from_user.id
    try:
        typed = update.message.reply_to_message.from_user.id
    except:
        return await update.message.delete()

    if clicked != typed:
        return await update.answer("That's not for you! 👀", show_alert=True)

    m = await update.message.edit("Searching... 💥")
    id = update.data.split("_")[-1]
    query = await search_imdb(id)
    channels = (await get_group(update.message.chat.id))["channels"]
    head = "<b>👇 I Have Searched Movie With Wrong Spelling But Take care next time 👇</b>\n\n"
    results = ""

    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption or "").split("\n")[0]
                if name in results:
                    continue
                # Use fuzzy matching for better accuracy
                if fuzz.partial_ratio(query.lower(), name.lower()) > 80:
                    results += f"<strong>🍿 {name}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"

        if not results:
            return await update.message.edit(
                "<blockquote>🥹 Sorry, no terabox link found ❌\n\nRequest Below 👇  Bot To Get Direct FILE📥</blockquote>",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("📥 Get Direct FILE Here 📥", url="https://t.me/Theater_Print_Movies_Search_bot")]]
                )
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
