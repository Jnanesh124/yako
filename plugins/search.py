import asyncio
from info import *
from utils import *
from time import time 
from client import User
from pyrogram import Client, filters 
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton 

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
    head = "👀 <b>Here are the results</b> 👀\n\n"
    buttons = []  # Collect buttons for inline markup
    results = ""

    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                
                # Add title and button to results
                results += f"🍿 <b>{name}</b>\n\n"
                buttons.append([InlineKeyboardButton(f"Download {name}", url=msg.link)])
        
        if not results:
            movies = await search_imdb(query)
            buttons = [[InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}")] for movie in movies]
            msg = await message.reply_text(
                text="😔 <b>Only Type Movie Name</b> 😔", 
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode="HTML"
            )
        else:
            # Combine titles and buttons in one message
            msg = await message.reply_text(
                text=head + results, 
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )

        # Auto-delete the message after the specified duration
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await msg.delete()

    except Exception as e:
        print(f"Error in search: {e}")  # Log the error for debugging


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
    head = "<b>👇 I Have Searched Movie With Wrong Spelling, Please Be Careful Next Time 👇</b>\n\n"
    buttons = []  # Collect buttons for inline markup
    results = ""

    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                
                # Add title and button to results
                results += f"🍿 <b>{name}</b>\n\n"
                buttons.append([InlineKeyboardButton(f"Download {name}", url=msg.link)])

        if not results:          
            return await update.message.edit(
                "🥹 <b>Sorry, no link found ❌</b>\n\nRequest the bot below 👇 to get the file 📥",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Get File Here 📥", url="https://t.me/Theater_Print_Movies_Search_bot")]]),
                parse_mode="HTML"
            )

        await update.message.edit(
            text=head + results, 
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )

        # Auto-delete the message after the specified duration
        await asyncio.sleep(AUTO_DELETE_DURATION)
        await update.message.delete()

    except Exception as e:
        await update.message.edit(f"❌ <b>Error:</b> `{e}`", parse_mode="HTML")


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
