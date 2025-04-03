from flask import Flask
from threading import Thread
import os
import asyncio
import discord
import requests
import logging
from discord.ext import commands
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from helpers import send_chunks

# Create the Flask app for the web interface
app = Flask(__name__)

@app.route('/')
def wake():
    return "I am awake!"
    
# Retrieve the Discord token from the environment
token = os.getenv("TOKEN")
logging.info(f"Token loaded: {bool(token)}")  # Should print True if your token is loaded

# Set up intents. Enable message_content if needed.
intents = discord.Intents.default()
intents.message_content = True  # Also enable this in the Discord Developer Portal.

# Create the bot instance with the specified command prefix and intents.
bot = commands.Bot(command_prefix="!", intents=intents)

# Global flag to track if the awake message has been sent
awake_message_sent = False

@bot.event
async def on_ready():
    channel = bot.get_channel(1354854476275650785)  # Replace with your actual channel ID (as an integer)
    if channel:
        await channel.send("I am awake!")


def run_web_server():
    app.run(host='0.0.0.0', port=10000)

# Start the Flask web server in a separate thread
web_thread = Thread(target=run_web_server)
web_thread.start()

async def main():
    logging.info("Loading extension: cogs.sync")
    await bot.load_extension("cogs.sync")
    logging.info("Starting bot...")
    await bot.start(token)

# Instead of storing just the channel name for a designer, we'll now store both the channel and a flag for full output.
designer_by_user = {}
# The dictionary will now be structured like:
# { user_id: { "channel": "petiteknit", "full": True/False } }

# Updated get_pattern_title function with a "full" parameter.
def get_pattern_title(url, full=False):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        if soup.title and soup.title.string:
            title = soup.title.string
            # Remove the " - Ravelry" suffix
            raw_title = title.replace(" - Ravelry", "").strip()
            # Always remove "Ravelry:" prefix
            if raw_title.startswith("Ravelry: "):
                raw_title = raw_title.replace("Ravelry: ", "")
            # When full flag is on, remove the word "pattern" from "pattern by"
            if full:
                raw_title = raw_title.replace("pattern by", "by")
            # Otherwise, strip out the "pattern by" part entirely.
            elif "pattern by" in raw_title:
                raw_title = raw_title.split(" pattern by")[0].strip()
            return raw_title
        else:
            return None
    except Exception as e:
        logging.info("Error fetching title:", e)
        return None

# Updated setdesigner command.
@bot.command()
async def setdesigner(ctx, *, designer):
    """
    Set the designer (forum channel name) for the user.
    If you add the word 'full' at the end of your input (e.g. "!setdesigner petiteknit full"),
    the bot will post the full title (keeping the 'by' section but stripping out 'pattern').
    """
    full_flag = False
    parts = designer.split()
    if parts[-1].lower() == "full":
        full_flag = True
        designer = " ".join(parts[:-1])
    designer_by_user[ctx.author.id] = {"channel": designer, "full": full_flag}
    flag_msg = " with full details (keeping the 'by' section without the word 'pattern')" if full_flag else ""
    await ctx.send(f"Designer set to **{designer}** for you{flag_msg}.")

@bot.command()
async def listalltags(ctx):
    output = "Available tags in all forum channels:\n"
    forum_channels = [c for c in ctx.guild.channels if c.type == discord.ChannelType.forum]

    if not forum_channels:
        await ctx.send("No forum channels found.")
        return

    for forum in forum_channels:
        output += f"\n**{forum.name}**:\n"
        if not forum.available_tags:
            output += "  (no tags)\n"
            continue
        for tag in forum.available_tags:
            output += f"  - {tag.name} (ID: {tag.id})\n"

    await send_chunks(ctx, output)

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user:
        return

    user_id = message.author.id
    if user_id not in designer_by_user:
        return  # Only respond if a designer is set

    user_designer = designer_by_user[user_id]
    channel_name = user_designer["channel"]
    full_flag = user_designer["full"]

    # Extract all links from the message
    links = [word for word in message.content.split() if word.startswith("http")]
    if not links:
        return

    forum_channel = discord.utils.get(message.guild.channels,
                                      name=channel_name,
                                      type=discord.ChannelType.forum)
    if not forum_channel:
        await message.channel.send(f"Forum channel **{channel_name}** not found.")
        return

    for link in links:
        title = get_pattern_title(link, full=full_flag)
        if title:
            await forum_channel.create_thread(name=title, content=link)
            await message.channel.send(f"Posted: **{title}** in {channel_name}")
        else:
            await message.channel.send(f"Could not fetch title for: {link}")
        await asyncio.sleep(0.5)

@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, 'on_error'):
        return
    error_msg = f"⚠️ An error occurred: `{str(error)}`"
    try:
        await ctx.send(error_msg)
    except discord.Forbidden:
        logging.info(f"Could not send error message to channel: {ctx.channel}")
    logging.info(f"Command error in {ctx.command}: {str(error)}")

async def main():
    logging.info("Loading extension: cogs.sync")
    await bot.load_extension("cogs.sync")
    logging.info("Starting bot...")
    await bot.start(token)

asyncio.run(main())
