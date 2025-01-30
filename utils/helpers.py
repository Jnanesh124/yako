import asyncio 
from info import *
from pyrogram import enums
from imdb import Cinemagoer
from pymongo.errors import DuplicateKeyError
from pyrogram.errors import UserNotParticipant
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton

dbclient = AsyncIOMotorClient(DATABASE_URI)
db       = dbclient["Channel-Filter"]
grp_col  = db["GROUPS"]
user_col = db["USERS"]
dlt_col  = db["Auto-Delete"]

ia = Cinemagoer()

async def add_group(group_id, group_name, user_name, user_id, channels, f_sub, verified):
    data = {"_id": group_id, "name":group_name, 
            "user_id":user_id, "user_name":user_name,
            "channels":channels, "f_sub":f_sub, "verified":verified}
    try:
       await grp_col.insert_one(data)
    except DuplicateKeyError:
       pass

async def get_group(chat_id):
    try:
        group = await db.groups.find_one({"chat_id": chat_id})
        return dict(group) if group else {}  # ✅ Return empty dictionary if not found
    except Exception as e:
        print(f"Error fetching group: {e}")
        return {}  # ✅ Return empty dictionary on error

async def update_group(id, new_data):
    data = {"_id":id}
    new_value = {"$set": new_data}
    await grp_col.update_one(data, new_value)

async def delete_group(id):
    data = {"_id":id}
    await grp_col.delete_one(data)
    
async def delete_user(id):
    data = {"_id":id}
    await user_col.delete_one(data)

async def get_groups():
    try:
        # Count the number of documents in the collection
        count = await grp_col.count_documents({})
        
        # If there are no documents, return an empty list
        if count == 0:
            return count, []
        
        # Fetch all documents from the collection
        cursor = grp_col.find({})
        
        # Convert the cursor to a list and return
        list = await cursor.to_list(length=count)
        return count, list
    except Exception as e:
        # Log or handle any errors that occur during the operation
        print(f"Error fetching groups: {str(e)}")
        return 0, []

async def add_user(id, name):
    data = {"_id":id, "name":name}
    try:
       await user_col.insert_one(data)
    except DuplicateKeyError:
       pass

async def get_users():
    count  = await user_col.count_documents({})
    cursor = user_col.find({})
    list   = await cursor.to_list(length=int(count))
    return count, list

async def save_dlt_message(chat_id, msg, time):
    data = {"chat_id": chat_id,
            "message_id": msg.id,
            "time": time}
    await dlt_col.insert_one(data)
   
async def get_all_dlt_data(time):
    data     = {"time":{"$lte":time}}
    count    = await dlt_col.count_documents(data)
    cursor   = dlt_col.find(data)
    all_data = await cursor.to_list(length=int(count))
    return all_data

async def delete_all_dlt_data(time):   
    data = {"time":{"$lte":time}}
    await dlt_col.delete_many(data)

async def search_imdb(query):
    try:
       int(query)
       movie = ia.get_movie(query)
       return movie["title"]
    except:
       movies = ia.search_movie(query, results=10)
       list = []
       for movie in movies:
           title = movie["title"]
           try: year = f" - {movie['year']}"
           except: year = ""
           list.append({"title":title, "year":year, "id":movie.movieID})
       return list

async def force_sub(bot, message):
    group = await get_group(message.chat.id)
    
    # Check if 'f_sub' key exists before accessing it
    if "f_sub" not in group:
        # Log or handle the case where 'f_sub' is missing
        await bot.send_message(chat_id=message.chat.id, text="Missing 'f_sub' key in group data.")
        return False
    
    f_sub = group["f_sub"]
    admin = group["user_id"]
    if f_sub == False:
        return True
    if message.from_user is None:
        return True 
    try:
        f_link = (await bot.get_chat(f_sub)).invite_link
        member = await bot.get_chat_member(f_sub, message.from_user.id)
        if member.status == enums.ChatMemberStatus.BANNED:
            await message.reply(f"ꜱᴏʀʀʏ {message.from_user.mention}!\n ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ, ʏᴏᴜ ᴡɪʟʟ ʙᴇ ʙᴀɴɴᴇᴅ ꜰʀᴏᴍ ʜᴇʀᴇ ᴡɪᴛʜɪɴ 10 ꜱᴇᴄᴏɴᴅꜱ")
            await asyncio.sleep(10)
            await bot.ban_chat_member(message.chat.id, message.from_user.id)
            return False       
    except UserNotParticipant:
        await bot.restrict_chat_member(chat_id=message.chat.id, 
                                       user_id=message.from_user.id,
                                       permissions=ChatPermissions(can_send_messages=False)
                                       )
        await message.reply(f"<b>👀 ʜɪ ᴅᴇᴀʀ {message.from_user.mention}!\n\n ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ Reques Movie ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ\n\nFirst u join And Subscribe my YouTube channel and Backup Group\n\n subscribe Here :- https://youtube.com/@Jnentertainment.?si=-xZOdUGBD3yxLjgW\n\n👇 Join Below Group 👇 after Click Try Again Button To Request Movie 🍿</b>", 
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ ᴊᴏɪɴ Group ✅", url=f_link)]]))
        await message.delete()
        return False
    except Exception as e:
        await bot.send_message(chat_id=admin, text=f"❌ Error in Fsub:\n`{str(e)}`")
        return False 
    else:
        return True

async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"
