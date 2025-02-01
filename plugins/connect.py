from info import *
from utils import *  # Import from utils_helper.py
from client import User
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus  # Correct import for user status

@Client.on_message(filters.group & filters.command("connect"))
async def connect(bot, message):
    m = await message.reply("Connecting...")
    bot_user = await User.get_me()  # Fetch bot details
    bot_username = bot_user.username or bot_user.mention  # Fix username error

    try:
        group = await get_group(message.chat.id) or {}
        user_id = group.get("user_id")
        user_name = group.get("user_name", "Unknown")
        verified = group.get("verified", False)
        channels = group.get("channels", [])
    except Exception as e:
        print(f"Error fetching group details: {e}")
        return await bot.leave_chat(message.chat.id)

    if not (await is_admin(bot, message.chat.id, message.from_user.id) or message.from_user.id in [user_id, 6605647659]):
        return await m.edit(f"Only {user_name} (Group Owner), group admins, or user 6605647659 can use this command 😁")

    if not verified:
        return await m.edit("This chat is not verified!\nUse /verify")

    try:
        channel = int(message.command[-1])
        if channel in channels:
            return await message.reply("This channel is already connected!")
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
    bot_user = await User.get_me()
    bot_username = bot_user.username or bot_user.mention

    try:
        group = await get_group(message.chat.id) or {}
        group_owner_id = group.get("user_id")  # Rename to avoid confusion
        user_name = group.get("user_name", "Unknown")
        verified = group.get("verified", False)
        channels = group.get("channels", [])
    except Exception as e:
        print(f"Error fetching group details: {e}")
        return await bot.leave_chat(message.chat.id)

    if not (await is_admin(bot, message.chat.id, message.from_user.id) or message.from_user.id in [group_owner_id, 6605647659]):
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
        chat = await bot.get_chat(channel)
        c_link = chat.invite_link

        # Check if the bot is a member of the channel
        try:
            await User.get_chat_member(channel, bot_user.id)
        except Exception as e:
            if "USER_NOT_PARTICIPANT" in str(e):
                # Bot is not a member of the channel, but we can still remove it from the database
                channels.remove(channel)
                await update_group(message.chat.id, {"channels": channels})
                return await m.edit("✅ The bot is not a member of the channel, but it has been successfully disconnected from the database.")
            else:
                raise e

        # Leave the channel
        await User.leave_chat(channel)
        channels.remove(channel)
    except Exception as e:
        if "CHANNEL_INVALID" in str(e) or "ID not found" in str(e):
            channels.remove(channel)
            await update_group(message.chat.id, {"channels": channels})
            return await m.edit("✅ The channel was banned or invalid, but it has been successfully disconnected from the database.")
        else:
            return await m.edit(f"❌ Error: {str(e)}\nMake sure {bot_username} is not banned there.")

    await update_group(message.chat.id, {"channels": channels})
    await m.edit(f"✅ Successfully disconnected from [{chat.title}]({c_link})!", disable_web_page_preview=True)

@Client.on_message(filters.command("connections") & filters.group)
async def connections(bot, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        group = await get_group(chat_id) or {}
        group_owner_id = group.get("user_id")  # Rename to avoid confusion
        user_name = group.get("user_name", "Unknown")
        verified = group.get("verified", False)
        channels = group.get("channels", [])

        # Check if the user is an admin or the group owner
        if not (await is_admin(bot, chat_id, user_id) or user_id == group_owner_id):
            return await message.reply_text(f"Only {user_name} (Group Owner) or group admins can use this command 😁")

        if not verified:
            return await message.reply_text("This chat is not verified!\nUse /verify")

        if not channels:
            return await message.reply_text("No channels are connected to this group.")

        # Build the list of connected channels
        text = "<b>Connected Channels:</b>\n"
        for channel_id in channels:
            try:
                chat = await bot.get_chat(channel_id)
                text += f"• <b>{chat.title}</b> (<code>{channel_id}</code>)\n"
            except Exception as e:
                print(f"Error fetching channel {channel_id}: {e}")
                text += f"• ❌ <code>{channel_id}</code> (Not Accessible)\n"

        await message.reply_text(text, disable_web_page_preview=True)

    except Exception as e:
        print(f"Error in /connections: {e}")
        await message.reply_text("❌ Error fetching connections. Please try again later.")
