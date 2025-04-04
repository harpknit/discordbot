import asyncio
import logging
import discord
from discord.ext import commands
from helpers import get_pattern_title

class RavelryCog(commands.Cog):
    def __init__(self, bot, designer_by_user):
        self.bot = bot
        self.designer_by_user = designer_by_user

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        user_id = message.author.id
        if user_id not in self.designer_by_user:
            return  # Only respond if a designer is set

        user_designer = self.designer_by_user[user_id]
        channel_name = user_designer["channel"]
        full_flag = user_designer["full"]

        # Extract links from message content
        links = [word for word in message.content.split() if word.startswith("http")]
        if not links:
            return

        forum_channel = discord.utils.get(
            message.guild.channels, name=channel_name, type=discord.ChannelType.forum
        )
        if not forum_channel:
            await message.channel.send(f"Forum channel **{channel_name}** not found.")
            return

        for link in links:
            title = get_pattern_title(link, full=full_flag)
            if title:
                try:
                    await forum_channel.create_thread(name=title, content=link)
                    await message.channel.send(f"Posted: **{title}** in {channel_name}")
                except Exception as e:
                    error_text = str(e)
                    if "A tag is required to create a forum post in this channel" in error_text:
                        await message.channel.send("A tag is required to create a forum post in this channel. Please update this setting or contact a mod.")
                    else:
                        logging.info(f"Exception occurred: {e}")
                        await message.channel.send(f"An error occurred: {e}")
            else:
                await message.channel.send(f"Could not fetch title for: {link}")
            await asyncio.sleep(0.5)

def setup(bot):
    # Pass the designer_by_user dictionary from your main file or shared module
    from main import designer_by_user  # Ensure circular imports are handled properly
    bot.add_cog(RavelryCog(bot, designer_by_user))
