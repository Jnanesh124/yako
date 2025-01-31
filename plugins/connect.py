from info import *
from utils import *
from client import User
from pyrogram import Client, filters
from pyrogram.types import ChatMember, ChatPrivileges

# Improved helper function to check admin status
async def is_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except Exception as e:
        print(f"Error checking admin status: {e}")  # Debugging
        return False

@Client.on_message(filters.group & filters.command("connect"))
async def connect(bot, message):
    m = await message.reply("Connecting...")
    bot_user = await User.get_me()  # Fetch bot details
    bot_username = bot_user.username or bot_user.mention  # Fixes username error

    try:
        group = await get_group(message.chat.id) or {}  # Prevent NoneType error
        user_id = group.get("user_id")
        user_name = group.get("user_name", "Unknown")
        verified = group.get("verified", False)
        channels = group.get("channels", [])
    except Exception as e:
        print(f"Error fetching group details: {e}")
        return await bot.leave_chat(message.chat.id)

    print(f"Message Sender ID: {message.from_user.id}, Group Owner ID: {user_id}")

    if not (await is_admin(bot, message.chat.id, message.from_user.id) or message.from_user.id == user_id or message.from_user.id == 6605647659):
        return await m.edit(f"Only {user_name} (Group Owner), group admins, or user 6605647659 can use this command 😁")

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
            return await m.edit(f"❌ Error: {str(e)}\nMake sure I'm an admin in that channel & this group and {bot_username} is not banned there.")

    await update_group(message.chat.id, {"channels": channels})
    await m.edit(f"✅ Successfully connected to [{chat.title}]({c_link})!", disable_web_page_preview=True)
    text = f"#NewConnection\n\nUser: {message.from_user.mention}\nGroup: [{group.title}]({g_link})\nChannel: [{chat.title}]({c_link})"
    await bot.send_message(chat_id=LOG_CHANNEL, text=text)

@Client.on_message(filters.group & filters.command("disconnect"))
async def disconnect(bot, message):
    m = await message.reply("Please wait...")
    bot_user = await User.get_me()  # Fetch bot details
    bot_username = bot_user.username or bot_user.mention  # Fix username error

    try:
        group = await get_group(message.chat.id) or {}  # Prevent NoneType error
        user_id = group.get("user_id")
        user_name = group.get("user_name", "Unknown")
        verified = group.get("verified", False)
        channels = group.get("channels", [])
    except Exception as e:
        print(f"Error fetching group details: {e}")
        return await bot.leave_chat(message.chat.id)

    print(f"Message Sender ID: {message.from_user.id}, Group Owner ID: {user_id}")

    if not (await is_admin(bot, message.chat.id, message.from_user.id) or message.from_user.id == user_id or message.from_user.id == 6605647659):
        return await m.edit(f"Only {user_name} (Group Owner), group admins, or user 6605647659 can use this command 😁")

    if not verified:
        return await m.edit("This chat is not verified!\nUse /verify")

    try:
        channel = int(message.command[-1])
        if channel not in channels:
            return await m.edit("This channel is not connected or check the Channel ID.")
    except ValueError:
        return await m.edit("❌ Incorrect format!\nUse /disconnect ChannelID")

    try:
        chat = await bot.get_chat(channel)  # Check if the channel is accessible
        c_link = chat.invite_link
        await User.leave_chat(channel)  # Try leaving the channel
        channels.remove(channel)  # Remove from database
    except Exception as e:
        if "CHANNEL_INVALID" in str(e) or "ID not found" in str(e):
            channels.remove(channel)
            await update_group(message.chat.id, {"channels": channels})
            return await m.edit(f"✅ The channel was banned or invalid, but it has been successfully disconnected from the database.")
        else:
            return await m.edit(f"❌ Error: {str(e)}\nMake sure {bot_username} is not banned there.")

    await update_group(message.chat.id, {"channels": channels})
    await m.edit(f"✅ Successfully disconnected from [{chat.title}]({c_link})!", disable_web_page_preview=True)

@Client.on_message(filters.command("connections") & filters.group)
async def connections(bot, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        # Fetch all admins (including the owner)
        admins = [admin.user.id async for admin in bot.get_chat_administrators(chat_id)]

        # Check if the user is an admin
        if user_id not in admins:
            return await message.reply_text("Only Group Owner or Admins can use this command 😁")

        # Fetch connected channels for the group
        group = await get_group(chat_id) or {}
        channels = group.get("channels", [])

        if not channels:
            return await message.reply_text("No channels are connected to this group.")

        text = "<b>Connected Channels:</b>\n"
        for ch in channels:
            try:
                chat = await bot.get_chat(ch)
                text += f"• <b>{chat.title}</b> (<code>{ch}</code>)\n"
            except Exception:
                text += f"• ❌ <code>{ch}</code> (Not Accessible)\n"

        await message.reply_text(text, disable_web_page_preview=True)

    except Exception as e:
        print(f"Error in /connections: {e}")
        await message.reply_text("❌ Error fetching connections.")
