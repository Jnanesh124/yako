import asyncio
from time import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from client import User  # Assuming this is how you import User from client
from utils import get_group, save_dlt_message, search_imdb, force_sub  # Import necessary functions from utils

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
    head = "👀 𝐎𝐧𝐥𝐢𝐧𝐞 𝐒𝐭𝐫𝐞𝐚𝐦𝐢𝐧𝐠 𝐋𝐢𝐧𝐤 👀\n\n"
    results = ""

    try:
       for channel in channels:
           async for msg in User.search_messages(chat_id=channel, query=query):
               name = (msg.text or msg.caption).split("\n")[0]
               if name in results:
                  continue 
               results += f"<strong>🍿 {name}<u>n━➣ {msg.link}</u>\n\n {text} {query} {msg}</strong>\n\n"                                                     

       if not results:
          movies = await search_imdb(query)
          buttons = []
          for movie in movies: 
              buttons.append([InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}")])
          msg = await message.reply("<strong>➪ 𝐮 𝐭𝐲𝐩𝐞𝐝 ❌ 𝐰𝐫𝐨𝐧𝐠 𝐦𝐨𝐯𝐢𝐞 𝐧𝐚𝐦𝐞 𝐬𝐨 𝐝𝐨𝐧'𝐭 𝐰𝐨𝐫𝐫𝐲\n➪ 𝐮 𝐜𝐚𝐧 𝐠𝐨 𝐭𝐨 𝐠𝐨𝐨𝐠𝐥𝐞 𝐚𝐧𝐝 𝐜𝐡𝐞𝐜𝐤 𝐚𝐧𝐝 𝐬𝐞𝐧𝐝  𝐡𝐞𝐫𝐞 👀\n➪ 𝐚𝐫𝐞 𝐬𝐞𝐥𝐞𝐜𝐭 𝐜𝐨𝐫𝐫𝐞𝐜𝐭 𝐦𝐨𝐯𝐢𝐞 𝐧𝐚𝐦𝐞 𝐢𝐧 𝐛𝐞𝐥𝐨𝐰 𝐚𝐩𝐭𝐢𝐨𝐧 👇</strong>", reply_markup=InlineKeyboardMarkup(buttons))
          await asyncio.sleep(30)
          await msg.delete()
       else:
          msg = await message.reply_text(text=head+results, disable_web_page_preview=True)
          await asyncio.sleep(40)
          await msg.delete()
           
       # Save message ID and deletion time
       _time = int(time()) + (15*60)
       await save_dlt_message(msg, _time)

       # Auto delete after 60 seconds
       await results.message.delete(700)

    except Exception as e:
        pass

@Client.on_callback_query(filters.regex(r"^recheck"))
async def recheck(bot, update):
    clicked = update.from_user.id
    try:      
       typed = update.message.reply_to_message.from_user.id
    except:
       return await update.message.delete(2)       
    if clicked != typed:
       return await update.answer("That's not for you! 👀", show_alert=True)

    m = await update.message.edit("𝐒𝐞𝐚𝐫𝐜𝐡𝐢𝐧𝐠 𝐅𝐨𝐫 𝐔𝐫 𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐌𝐨𝐯𝐢𝐞 𝐖𝐚𝐢𝐭....⏳")
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
               results += f"<strong>🍿 {name}</b>\n\n━➣ {msg.link}</strong>\n\n"

       if not results:          
          return await update.message.edit("<strong>🫵 𝐍𝐨 𝐨𝐧𝐥𝐢𝐧𝐞 𝐒𝐭𝐫𝐞𝐚𝐦𝐢𝐧𝐠 𝐥𝐢𝐧𝐤 🧲 𝐅𝐨𝐮𝐧𝐝 ⏳</strong>\n\n<strong>💬 𝐒𝐨 𝐆𝐞𝐭 𝐃𝐢𝐫𝐞𝐜𝐭𝐞 𝐅𝐢𝐥𝐞 📁 𝐈𝐧 𝐁𝐞𝐥𝐨𝐰 𝐁𝐨𝐭 👇</strong>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝 𝐅𝐢𝐥𝐞 ✅", url=f"t.me/Rockers_ott_movie_link_bot")]]))

       await update.message.edit(text=head + results, disable_web_page_preview=True)

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
    id    = update.data.split("_")[1]
    name  = await search_imdb(id)
    url   = "https://www.imdb.com/title/tt" + id
    text  = f"#RequestFromYourGroup\n\nName: {name}\nIMDb: {url}"
    await bot.send_message(chat_id=admin, text=text, disable_web_page_preview=True)
    await update.answer("✅ Request Sent To Admin", show_alert=True)
    await update.message.delete(60)
