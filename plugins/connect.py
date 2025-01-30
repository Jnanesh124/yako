from info import *
from utils import *
from client import User
from pyrogram import Client, filters
from pyrogram.types import ChatMember

# Improved helper function to check admin status
async def is_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status in ["administrator", "creator"]:
            return True
        return False
    except Exception as e:
        print(f"Error checking admin status: {e}")  # Debugging
        return False

@Client.on_message(filters.group & filters.command("connect"))
async def connect(bot, message):
    m = await message.reply("Connecting...")
    user = await User.get_me()
    try:
        group = await get_group(message.chat.id)
        user_id = group["user_id"]
        user_name = group["user_name"]
        verified = group["verified"]
        channels = group["channels"].copy()
    except Exception as e:
        print(f"Error fetching group details: {e}")
        return await bot.leave_chat(message.chat.id)
    
    # Debugging: Log the user ID and the group owner ID
    print(f"Message Sender ID: {message.from_user.id}, Group Owner ID: {user_id}")
    
    # Check if the user is the group owner, an admin, or the special user with ID 6605647659
    if not (await is_admin(bot, message.chat.id, message.from_user.id) or message.from_user.id == user_id or message.from_user.id == 6605647659):
        return await m.edit(f"Only {user_name} (Group Owner), group admins, or the user with ID 6605647659 can use this command 😁")
    
    if not verified:
        return await m.edit("This chat is not verified!\nUse /verify")
    
    try:
        channel = int(message.command[-1])
        if channel in channels:
            return await message.reply("This channel is already connected! You can't connect it again.")
        channels.append(channel)
    except ValueError:
        return await m.edit("❌ Incorrect format!\nUse /connect ChannelID")
    
    try:
        chat = await bot.get_chat(channel)
        group = await bot.get_chat(message.chat.id)
        c_link = chat.invite_link
        g_link = group.invite_link
        await User.join_chat(c_link)
    except Exception as e:
        if "The user is already a participant" in str(e):
            pass
        else:
            text = (f"❌ Error: {str(e)}\nMake sure I'm an admin in that channel & this group "
                    f"with all permissions and {(user.username or user.mention)} is not banned there.")
            return await m.edit(text)
    
    await update_group(message.chat.id, {"channels": channels})
    await m.edit(f"✅ Successfully connected to [{chat.title}]({c_link})!", disable_web_page_preview=True)
    text = f"#NewConnection\n\nUser: {message.from_user.mention}\nGroup: [{group.title}]({g_link})\nChannel: [{chat.title}]({c_link})"
    await bot.send_message(chat_id=LOG_CHANNEL, text=text)

@Client.on_message(filters.group & filters.command("disconnect"))
async def disconnect(bot, message):
    m = await message.reply("Please wait...")
    try:
        group = await get_group(message.chat.id)
        user_id = group["user_id"]
        user_name = group["user_name"]
        verified = group["verified"]
        channels = group["channels"].copy()
    except Exception as e:
        print(f"Error fetching group details: {e}")
        return await bot.leave_chat(message.chat.id)
    
    # Debugging: Log the user ID and the group owner ID
    print(f"Message Sender ID: {message.from_user.id}, Group Owner ID: {user_id}")
    
    # Check if the user is the group owner, an admin, or the special user with ID 6605647659
    if not (await is_admin(bot, message.chat.id, message.from_user.id) or message.from_user.id == user_id or message.from_user.id == 6605647659):
        return await m.edit(f"Only {user_name} (Group Owner), group admins, or the user with ID 6605647659 can use this command 😁")
    
    if not verified:
        return await m.edit("This chat is not verified!\nUse /verify")
    
    try:
        channel = int(message.command[-1])
        if channel not in channels:
            return await m.edit("This channel is not connected or check the Channel ID.")
        channels.remove(channel)
    except ValueError:
        return await m.edit("❌ Incorrect format!\nUse /disconnect ChannelID")
    
    try:
        chat = await bot.get_chat(channel)
        group = await bot.get_chat(message.chat.id)
        c_link = chat.invite_link
        g_link = group.invite_link
        await User.leave_chat(channel)
    except Exception as e:
        text = (f"❌ Error: {str(e)}\nMake sure I'm an admin in that channel & this group "
                f"with all permissions and {(User.username or user.mention)} is not banned there.")
        return await m.edit(text)
    
    await update_group(message.chat.id, {"channels": channels})
    await m.edit(f"✅ Successfully disconnected from [{chat.title}]({c_link})!", disable_web_page_preview=True)
    text = f"#DisConnection\n\nUser: {message.from_user.mention}\nGroup: [{group.title}]({g_link})\nChannel: [{chat.title}]({c_link})"
    await bot.send_message(chat_id=LOG_CHANNEL, text=text)

@Client.on_message(filters.group & filters.command("connections"))
async def connections(bot, message):
    group = await get_group(message.chat.id)
    user_id = group["user_id"]
    user_name = group["user_name"]
    channels = group["channels"]
    f_sub = group["f_sub"]
    if not (await is_admin(bot, message.chat.id, message.from_user.id) or message.from_user.id == user_id):
        return await message.reply(f"Only {user_name} (Group Owner) or group admins can use this command 😁")
    if not channels:
        return await message.reply("This group is currently not connected to any channels!\nConnect one using /connect")
    text = "This Group is currently connected to:\n\n"
    for channel in channels:
        try:
            chat = await bot.get_chat(channel)
            name = chat.title
            link = chat.invite_link
            text += f"🔗 Connected Channel - [{name}]({link})\n"
        except Exception as e:
            await message.reply(f"❌ Error in {channel}:\n{e}")
    if f_sub:
        try:
            f_chat = await bot.get_chat(f_sub)
            f_title = f_chat.title
            f_link = f_chat.invite_link
            text += f"\nFSub: [{f_title}]({f_link})"
        except Exception as e:
            await message.reply(f"❌ Error in FSub ({f_sub})\n{e}")
    await message.reply(text=text, disable_web_page_preview=True)
