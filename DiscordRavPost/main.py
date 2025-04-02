import os
import asyncio
import discord
import requests
import logging
from discord.ext import commands
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from helpers import send_chunks
logging.basicConfig(level=logging.INFO)

logging.info("Starting main.py...")
load_dotenv()  # Load .env variables

# Check if TOKEN is loaded
token = os.getenv("TOKEN")
logging.info(f"Token loaded: {bool(token)}")# Should print True if your token is loaded

# Set up intents. Enable message_content if needed.
intents = discord.Intents.default()
intents.message_content = True  # Also enable this in the Discord Developer Portal.

# Create the bot instance with the specified command prefix and intents.
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    logging.info(f'{bot.user} is online!')

# Store designer channel per user for posting patters
designer_by_user = {}


# Extract just the pattern title from a Ravelry link
def get_pattern_title(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        if soup.title and soup.title.string:
            title = soup.title.string
            raw_title = title.replace(" - Ravelry", "").strip()
            if "pattern by" in raw_title:
                raw_title = raw_title.split(" pattern by")[0].strip()
            if raw_title.startswith("Ravelry: "):
                raw_title = raw_title.replace("Ravelry: ", "")
            return raw_title
        else:
            return None
    except Exception as e:
        logging.info("Error fetching title:", e)
        return None


@bot.command()
async def setdesigner(ctx, *, designer):
    designer_by_user[ctx.author.id] = designer
    await ctx.send(f"Designer set to **{designer}** for you.")


@bot.command()
async def listalltags(ctx):
    output = "Available tags in all forum channels:\n"

    forum_channels = [
        c for c in ctx.guild.channels if c.type == discord.ChannelType.forum
    ]

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

    designer = designer_by_user[user_id]

    # Extract all links from the message
    links = [
        word for word in message.content.split() if word.startswith("http")
    ]

    if not links:
        return

    forum_channel = discord.utils.get(message.guild.channels,
                                      name=designer,
                                      type=discord.ChannelType.forum)

    if not forum_channel:
        await message.channel.send(f"Forum channel **{designer}** not found.")
        return

    for link in links:
        title = get_pattern_title(link)
        if title:
            await forum_channel.create_thread(name=title, content=link)
            await message.channel.send(f"Posted: **{title}** in {designer}")
        else:
            await message.channel.send(f"Could not fetch title for: {link}")
            await asyncio.sleep(0.5)

@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, 'on_error'):
        # Don't interfere with custom per-command error handlers
        return

    error_msg = f"⚠️ An error occurred: `{str(error)}`"
    try:
        await ctx.send(error_msg)
    except discord.Forbidden:
        # Can't send messages in the channel
        logging.info(f"Could not send error message to channel: {ctx.channel}")
    logging.info(f"Command error in {ctx.command}: {str(error)}")

async def main():
    logging.info("Loading extension: cogs.sync")
    await bot.load_extension("cogs.sync")
    logging.info("Starting bot...")
    await bot.start(token)
asyncio.run(main())
