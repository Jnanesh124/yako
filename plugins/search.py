import asyncio
from info import *
from utils import *
from time import time
from client import User
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Auto-delete duration in seconds
AUTO_DELETE_DURATION = 60  # Adjust as needed

@Client.on_message(filters.text & (filters.group | filters.private) & ~filters.command(["verify", "connect", "id"]))
async def live_search(bot, message):
    query = message.text
    channels = [-100123789, -1008124797890]  # Replace with your channel IDs
    is_group = message.chat.type in ["group", "supergroup"]
    reply_head = "<b>🔍 Searching for your query...</b>\n\n"
    live_log = "🔎 <b>Searching Logs:</b>\n\n"

    # Send a "Searching" message
    progress_msg = await message.reply_text(reply_head, disable_web_page_preview=True)

    results = ""
    try:
        # Log and Search in Channels
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                link = f"<a href='{msg.link}'>Download</a>"
                results += f"🍿 <strong>{name}</strong> 👉🏻 {link}\n\n"

                # Update live logs
                live_log += f"✅ Found in {channel}: {name}\n"
                await progress_msg.edit_text(live_log + "\n<b>Searching...</b>")

        # If no results found
        if not results:
            live_log += "❌ No matches found in the channels.\n"
            await progress_msg.edit_text(
                f"{live_log}\n<b>🥹 Sorry, no matches found. Check the movie name and try again.</b>",
                disable_web_page_preview=True,
            )
        else:
            # Final result
            final_message = f"<b>👀 Search Results:</b>\n\n{results}"
            await progress_msg.edit_text(final_message, disable_web_page_preview=True)

        # Auto-delete the message after the specified duration
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await progress_msg.delete()

    except Exception as e:
        print(f"Error in live_search: {e}")
        await progress_msg.edit_text(f"❌ Error: {e}")


@Client.on_callback_query(filters.regex(r"^recheck"))
async def recheck(bot, update):
    clicked = update.from_user.id
    try:
        typed = update.message.reply_to_message.from_user.id
    except:
        return await update.message.delete()

    if clicked != typed:
        return await update.answer("That's not for you! 👀", show_alert=True)

    m = await update.message.edit("Searching...💥")
    id = update.data.split("_")[-1]
    query = await search_imdb(id)
    channels = (await get_group(update.message.chat.id))["channels"]
    head = "<b>👇 Re-checked Results Below 👇</b>\n\n"
    results = ""

    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                results += f"<strong>🍿 {name}</strong>\n<strong>👉🏻 <a href='{msg.link}'>DOWNLOAD</a> 👈🏻</strong>\n\n"

        if not results:
            return await update.message.edit(
                "<blockquote>🥹 Sorry, no terabox link found ❌\n\nRequest Below 👇 Bot To Get Direct FILE📥</blockquote>",
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
