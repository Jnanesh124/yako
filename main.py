from client import Bot
from app import run_bot  # Import the function to run the Pyrogram bot

if __name__ == "__main__":
    print("Bot and Flask Server Started 👍")
    
    # Start the bot in a separate thread so Flask can run in parallel
    run_bot()  # Run the Pyrogram bot asynchronously
