import asyncio
from time import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from client import User  # Assuming this is correctly imported

# Your other imports and setup here

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
    head = "<u>👀 𝐎𝐧𝐥𝐢𝐧𝐞 𝐒𝐭𝐫𝐞𝐚𝐦𝐢𝐧𝐠 𝐋𝐢𝐧𝐤 👀</u>\n\n"
    results = ""
    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                results += f"<b>🍿 {name}\n🔗 {msg.link}</b>\n\n"

        if not results:
            movies = await search_imdb(query)
            buttons = []
            for movie in movies:
                buttons.append([InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}")])
            msg = await message.reply("<b>only Type Movie Name 🤐</b>", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            msg = await message.reply_text(text=head + results, disable_web_page_preview=True)

        # Schedule message for deletion after 30 seconds
        delete_time = int(time()) + 30
        await save_dlt_message(msg, delete_time)

    except Exception as e:
        await asyncio.sleep(30)  # Retry after 30 seconds on exception
        await msg.delete()

@Client.on_callback_query(filters.regex(r"^recheck"))
async def recheck(bot, update):
    clicked = update.from_user.id
    try:
        typed = update.message.reply_to_message.from_user.id
    except:
        return await update.message.delete(2)
    if clicked != typed:
        return await update.answer("That's not for you! 👀", show_alert=True)

    m = await update.message.edit("𝐒𝐞𝐚𝐫𝐜𝐡𝐢𝐧𝐠 𝐅𝐨𝐫 𝐔𝐫 𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐌𝐨𝐯𝐢𝐞 𝐖𝐚𝐢𝐭 🔎")
    id = update.data.split("_")[-1]
    query = await search_imdb(id)
    channels = (await get_group(update.message.chat.id))["channels"]
    head = "<u>👇 𝐓𝐡𝐢𝐬 𝐢𝐬 𝐓𝐡𝐞 𝐌𝐨𝐯𝐢𝐞 𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞 𝐑𝐞𝐢𝐠𝐡𝐭 𝐊𝐧𝐨𝐰 👇</u>\n\n"
    results = ""
    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name in results:
                    continue
                results += f"<b>🍿 {name}</b>\n\n🔗 {msg.link}</b>\n\n"
        if not results:
            return await update.message.edit("<b>𝐍𝐨 𝐎𝐧𝐥𝐢𝐧𝐞 #𝐒𝐭𝐫𝐞𝐚𝐦𝐢𝐧𝐠 𝐋𝐢𝐧𝐤 𝐅𝐨𝐮𝐧𝐝 𝐑𝐞𝐢𝐠𝐡𝐭 𝐊𝐧𝐨𝐰 🥺 𝐒𝐨 𝐆𝐞𝐭 𝐃𝐢𝐫𝐞𝐜𝐭 𝐅𝐢𝐥𝐞 📁 𝐀𝐬𝐤 𝐓𝐡𝐢𝐬 𝐌𝐨𝐯𝐢𝐞 𝐀𝐠𝐚𝐢𝐧 𝐢𝐧 𝐁𝐞𝐥𝐨𝐰 𝐁𝐨𝐭 𝐔 𝐆𝐞𝐭 𝐔𝐫 𝐌𝐨𝐯𝐢𝐞 𝐅𝐢𝐥𝐞</b>\n\n<b>ನೀನು ಕೇಳಿದ ಸಿನಿಮಾ 𝐎𝐧𝐥𝐢𝐧𝐞 #𝐒𝐭𝐫𝐞𝐚𝐦𝐢𝐧𝐠 𝐋𝐢𝐧𝐤 ಲಭ್ಯ ಇಲ್ಲ ಇಗಿನ ಸಮಯ ದಲ್ಲಿ ಅದಕ್ಕೆ ನೆರ  𝐅𝐢𝐥𝐞 𝐁𝐞𝐥𝐨𝐰 𝐁𝐨𝐭 ಅಲ್ಲಿ ಮತ್ತೆ 𝐭𝐲𝐩𝐞 ಮಾಡಿ 𝐅𝐢𝐥𝐞 ಬರುತ್ತದೆ</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📁 Get Direct Movie File Here 📁", url=f"t.me/Rockers_ott_movie_link_bot")]]))
        
        await update.message.edit(text=head + results, disable_web_page_preview=True)
        
        # Schedule message for deletion after 60 seconds
        delete_time = int(time()) + 60
        await save_dlt_message(update.message, delete_time)

    except Exception as e:
        await update.message.edit(f"❌ Error: `{e}`")

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
    
    await bot.send_message(chat_id=admin, text=text, disable_web_page_preview=True)
    await update.answer("✅ Request Sent To Admin", show_alert=True)
    
    # Schedule message for deletion after 60 seconds
    delete_time = int(time()) + 60
    await save_dlt_message(update.message, delete_time)
