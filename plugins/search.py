import asyncio
from fuzzywuzzy import process
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
from collections import defaultdict

# Force-subscription channels
FORCE_SUB_CHANNELS = ["@ROCKERSBACKUP", "@JN2FLIX"]

# Pre-defined main channels for PM searches
main_channels = [
    -1002051432955,  # Example main channel 1
    -1001359763936,  # Example main channel 2
]

# Data storage for group-connected channels
group_channels = defaultdict(list)  # Stores connected channels for groups
group_admins = {}  # Stores the admin user ID for each group
pending_requests = defaultdict(list)  # Tracks pending movie requests for each group
group_access_status = defaultdict(bool)  # Stores whether a group admin has completed the force-sub process

# Define the bot's credentials
BOT_TOKEN = "YOUR_BOT_TOKEN"
API_ID = "29942004"
API_HASH = "6765313019:AAHYLXnKN_q5dhznb-4IuLddejkCFleIUg8"

# Initialize the app (Pyrogram Client)
app = Client("movie_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

def clean_query(query):
    """
    Clean a user's search query by removing unwanted parts.
    """
    query = re.sub(r"@\S+|https?://\S+|www\.\S+", "", query)  # Remove links and mentions
    ignored_words = ["please", "send", "file", "movie", "link", "the", "a", "an", "season"]
    query = " ".join(word for word in query.split() if word.lower() not in ignored_words)
    return query.strip()

async def check_subscription(client, user_id):
    """
    Verify if the user is subscribed to all the required channels.
    """
    for channel in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception:
            return False
    return True

async def notify_admin_on_channel_issue(client, group_id, channel_id, issue_type):
    """
    Notify the group admin in PM about a channel issue (removed or banned).
    """
    admin_id = group_admins.get(group_id)
    if admin_id:
        if issue_type == "removed":
            message = f"⚠️ The bot was removed from the connected channel `{channel_id}` in your group."
        elif issue_type == "banned":
            message = f"⚠️ The bot was banned from the connected channel `{channel_id}` in your group."
        await client.send_message(admin_id, message)

@app.on_message(filters.command("connect"))
async def connect_channel(client, message):
    """
    Command to connect a channel to a group.
    """
    group_id = message.chat.id
    admin_id = message.from_user.id
    group_admins[group_id] = admin_id  # Save the admin ID for the group

    if not group_access_status[group_id]:
        await message.reply(
            f"⚠️ Please join the following channels to use this bot in your group:\n"
            f"1. [ROCKERS BACKUP]({FORCE_SUB_CHANNELS[0]})\n"
            f"2. [JN2FLIX]({FORCE_SUB_CHANNELS[1]})\n\n"
            "Once done, type `/ijoined`.",
            disable_web_page_preview=True
        )
        return

    if not message.text.split()[1:]:
        await message.reply("Please provide a channel ID to connect. Example: `/connect -1001234567890`")
        return

    channel_id = message.text.split()[1]
    group_channels[group_id].append(channel_id)
    await message.reply(f"✅ Channel {channel_id} connected successfully.")

@app.on_message(filters.command("disconnect"))
async def disconnect_channel(client, message):
    """
    Command to disconnect a channel from a group.
    """
    group_id = message.chat.id
    if not message.text.split()[1:]:
        await message.reply("Please provide a channel ID to disconnect. Example: `/disconnect -1001234567890`")
        return

    channel_id = message.text.split()[1]
    if channel_id in group_channels[group_id]:
        group_channels[group_id].remove(channel_id)
        await message.reply(f"✅ Channel {channel_id} disconnected successfully.")
    else:
        await message.reply(f"❌ Channel {channel_id} is not connected to this group.")

@app.on_message(filters.command("connections"))
async def show_connections(client, message):
    """
    Command to list all connected channels for a group.
    """
    group_id = message.chat.id
    channels = group_channels.get(group_id, [])
    if channels:
        await message.reply("📚 Connected channels:\n" + "\n".join(channels))
    else:
        await message.reply("❌ No channels are connected to this group.")

@app.on_message(filters.command("ijoined"))
async def verify_subscription(client, message):
    """
    Command to verify if a group admin has joined the required channels.
    """
    group_id = message.chat.id
    admin_id = message.from_user.id

    if not (await check_subscription(client, admin_id)):
        await message.reply(
            "⚠️ You have not joined the required channels:\n"
            f"1. [ROCKERS BACKUP]({FORCE_SUB_CHANNELS[0]})\n"
            f"2. [JN2FLIX]({FORCE_SUB_CHANNELS[1]})",
            disable_web_page_preview=True
        )
        return

    group_access_status[group_id] = True
    await message.reply("✅ You have successfully completed the verification process. You can now connect channels.")

@app.on_message(filters.text & filters.group)
async def handle_channel_issues(client, message):
    """
    Monitor bot's presence in connected channels and notify admins of issues.
    """
    group_id = message.chat.id
    channels = group_channels.get(group_id, [])

    for channel_id in channels:
        try:
            # Test if the bot is still in the channel
            await client.get_chat(channel_id)
        except Exception as e:
            issue_type = "removed" if "chat not found" in str(e).lower() else "banned"
            await notify_admin_on_channel_issue(client, group_id, channel_id, issue_type)
            group_channels[group_id].remove(channel_id)  # Remove the problematic channel

@app.on_message(filters.text & filters.group)
async def search_movies(client, message):
    """
    Command to handle fuzzy search for movie names across connected channels.
    """
    query = message.text.strip()
    if not query or query.startswith("/"):
        return

    # Clean up the query
    cleaned_query = clean_query(query)

    if not cleaned_query:
        return  # No relevant query

    results = []
    group_id = message.chat.id
    channels = group_channels.get(group_id, [])

    # Collect movie titles from all connected channels
    all_movies = []
    for channel_id in channels:
        try:
            async for msg in client.search_messages(channel_id, query=cleaned_query):
                if msg.text:
                    title = msg.text.split("\n")[0]  # Assume the title is the first line
                    all_movies.append(title)
        except Exception as e:
            print(f"Error accessing channel {channel_id}: {e}")

    # Fuzzy search for the best matches from the collected movie list
    matched_results = process.extract(cleaned_query, all_movies, limit=5)
    for result in matched_results:
        title, score = result
        if score >= 75:  # Match threshold
            results.append(f"🍿 {title}\n👉 [Download]({message.link})")

    # Send the search results
    if results:
        await message.reply("\n".join(results))
    else:
        await message.reply("No matching movies found.")

# Run the bot
app.run()
