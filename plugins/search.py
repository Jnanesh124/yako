import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import ChannelPrivate, PeerIdInvalid, FloodWait
import difflib  # For fuzzy matching

STORAGE_CHANNEL = -1002051432955  # Define your storage channel using channel ID
MAX_BUTTON_TEXT_LENGTH = 64  # Telegram's max button text length

def token_match(query, movie_name):
    """Perform fuzzy matching to find if the query matches the movie name."""
    query_tokens = query.lower().split()
    movie_tokens = movie_name.lower().split()

    matched_tokens = 0
    for token in query_tokens:
        for movie_token in movie_tokens:
            similarity = difflib.SequenceMatcher(None, token, movie_token).ratio()
            if similarity > 0.7:
                matched_tokens += 1
                break

    return matched_tokens >= len(query_tokens) // 2

def format_title_for_button(title):
    """Format long movie titles so they fit in a button."""
    if len(title) <= MAX_BUTTON_TEXT_LENGTH:
        return title
    
    words = title.split()  # Split title into words
    new_title = ""
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > MAX_BUTTON_TEXT_LENGTH:  
            new_title += "\n"
            current_length = 0  
        new_title += word + " "  
        current_length += len(word) + 1  
    
    return new_title.strip()

@Client.on_message(filters.text & filters.group & filters.incoming & ~filters.command(["verify", "connect", "id"]))
async def search(bot, message):
    """Search for a movie based on user input and forward the found posts to the storage channel."""
    query = message.text.lower()
    head = "<blockquote>👀 Here are the results 👀</blockquote>\n\n"
    buttons = []

    channels = (await get_group(message.chat.id))["channels"]
    if not channels:
        return

    try:
        # Search in connected channels
        for channel in channels:
            try:
                async for msg in bot.search_messages(chat_id=channel, query=query):
                    # Ensure the message is valid and has the message_id attribute
                    if hasattr(msg, 'message_id') and msg.message_id:
                        name = (msg.text or msg.caption).split("\n")[0]

                        # Forward the found post to storage channel
                        stored_message = await bot.forward_messages(STORAGE_CHANNEL, channel, msg.message_id)
                        
                        # Generate special access link for the stored post
                        stored_link = f"https://t.me/Rockers_Postsearch_Bot?start={stored_message.message_id}"

                        # Add button with the link
                        formatted_title = format_title_for_button(name)
                        buttons.append([InlineKeyboardButton(f"🍿 {formatted_title}", url=stored_link)])

            except (ChannelPrivate, PeerIdInvalid) as e:
                print(f"Error accessing channel {channel}: {e}")
                continue
            except Exception as e:
                print(f"Error accessing channel {channel}: {e}")
                continue

        if buttons:
            await message.reply(
                text=head,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await message.reply("🥹 Sorry, no results found.")

        await asyncio.sleep(60)  # Auto delete after 60 seconds
        await message.delete()

    except Exception as e:
        print(f"Error in search: {e}")

@Client.on_message(filters.document & filters.group)
async def store_file(bot, message):
    """Store and forward files to the storage channel with a special access link."""
    try:
        # Check if message is a file and store it
        file = message.document
        if file:
            file_link = await bot.get_file(file.file_id)

            # Forward the file to the storage channel
            stored_message = await bot.send_document(
                STORAGE_CHANNEL,  # Numeric channel ID
                file_link.file_url,
                caption=f"📥 File stored: {file.file_name}",
            )

            # Generate special access link for the stored file
            storage_link = f"https://t.me/Rockers_Postsearch_Bot?start={stored_message.message_id}"
            
            # Send the generated storage link back to the user
            await message.reply(f"✅ File has been stored! You can access it here: {storage_link}")

    except Exception as e:
        print(f"Error storing file: {e}")
        await message.reply("❌ Failed to store file.")

# Define helper functions for searching, forwarding, and creating buttons
async def get_group(chat_id):
    """Retrieve connected channels and group settings."""
    # Your logic here to fetch group data, such as connected channels
    return {"channels": [-1001775543467, -1001654685875, -1001359763936]}  # Example channel IDs

async def search_imdb(query):
    """Search for movies using IMDb API (you need to implement or use an API)."""
    # Your logic here to search IMDb or implement the search
    return [{"id": "tt1234567", "title": "KGF 1"}, {"id": "tt7654321", "title": "KGF 2"}]  # Example IMDb results
