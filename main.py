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
from helpers import get_pattern_title
from helpers import designer_by_user

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
    logging.info("Loading extensions...")
    await bot.load_extension("cogs.sync")
    await bot.load_extension("cogs.designer")
    await bot.load_extension("cogs.ravelry")
    logging.info("Starting bot...")
    await bot.start(token)


# The dictionary will now be structured like:
# { user_id: { "channel": "petiteknit", "full": True/False } }


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
