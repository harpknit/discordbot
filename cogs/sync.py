import discord
from discord.ext import commands
from helpers import send_chunks
import asyncio

class SyncCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def syncchannelpermissions(self, ctx, *, category: str):
        # (Copy your current code for syncchannelpermissions here)
        target_category = discord.utils.get(ctx.guild.categories, name=category)
        if not target_category:
            await ctx.send(f"Category '{category}' not found.")
            return

        updated = []
        for channel in target_category.channels:
            try:
                await channel.edit(sync_permissions=True)
                updated.append(channel.name)
            except discord.Forbidden:
                await ctx.send(f"Missing access to sync '{channel.name}' — skipping.")
            except Exception as e:
                await ctx.send(f"Error syncing '{channel.name}': {str(e)}")

        await ctx.send(f"✅ Synced permissions for {len(updated)} channel(s) in '{category}'.")

    @commands.command()
    async def synctag(self, ctx, origin_name: str, target_name: str, *, mode: str = ""):
        """Sync tags from one forum channel to another forum channel."""
        dry_run = mode.lower() == "dry"
        changes_log = []

        origin_forum = discord.utils.get(ctx.guild.channels,
                                         name=origin_name,
                                         type=discord.ChannelType.forum)
        target_forum = discord.utils.get(ctx.guild.channels,
                                         name=target_name,
                                         type=discord.ChannelType.forum)

        if not origin_forum or not target_forum:
            await ctx.send(
                f"Could not find one or both forum channels: `{origin_name}`, `{target_name}`."
            )
            return

        origin_tags = origin_forum.available_tags
        if not origin_tags:
            await ctx.send(f"No tags found in origin forum '{origin_name}'.")
            return

        added = []
        existing_tag_names = [t.name.lower() for t in target_forum.available_tags]

        for tag in origin_tags:
            if tag.name.lower() not in existing_tag_names:
                if dry_run:
                    added.append(tag.name + " (dry)")
                else:
                    try:
                        await target_forum.create_tag(name=tag.name,
                                                      emoji=tag.emoji,
                                                      moderated=tag.moderated)
                        added.append(tag.name)
                    except discord.Forbidden:
                        added.append(f"{tag.name} (forbidden)")
                    except Exception as e:
                        added.append(f"{tag.name} (error: {str(e)})")

        if added:
            changes_log.append(
                f"- {target_forum.name}: would add {len(added)} tag(s) ({', '.join(added)})"
                if dry_run else
                f"- {target_forum.name}: added {len(added)} tag(s) ({', '.join(added)})"
            )
        else:
            changes_log.append(f"- {target_forum.name}: no changes")

        await ctx.send("\n".join(changes_log))

    @commands.command()
    async def syncalltags(self, ctx, origin_name: str,  *args):
        """Sync tags from one forum channel to all others in a category."""
        if not args:
            await ctx.send("Please specify a target category name.")
            return

        dry_run = args[-1].lower() == "dry"
        if dry_run:
            target_category_name = " ".join(args[:-1])
        else:
            target_category_name = " ".join(args)

        changes_log = []

        origin_forum = discord.utils.get(ctx.guild.channels,
                                         name=origin_name,
                                         type=discord.ChannelType.forum)
        if not origin_forum:
            await ctx.send(f"Source forum channel '{origin_name}' not found.")
            return

        origin_tags = origin_forum.available_tags
        if not origin_tags:
            await ctx.send(f"No tags found in source forum '{origin_name}'.")
            return

        target_forums = [
            ch for ch in ctx.guild.channels if ch.type == discord.ChannelType.forum
            and ch.category and ch.category.name == target_category_name
        ]

        if not target_forums:
            await ctx.send(
                f"No forum channels found in category '{target_category_name}'.")
            return

        for forum in target_forums:
            added = []
            existing_tag_names = [t.name.lower() for t in forum.available_tags]

            for tag in origin_tags:
                if tag.name.lower() not in existing_tag_names:
                    if dry_run:
                        added.append(tag.name + " (dry)")
                    else:
                        try:
                            await forum.create_tag(name=tag.name,
                                                   emoji=tag.emoji,
                                                   moderated=tag.moderated)
                            added.append(tag.name)
                            await asyncio.sleep(0.5)  # <-- delay added here
                        except discord.Forbidden:
                            added.append(f"{tag.name} (forbidden)")
                        except Exception as e:
                            added.append(f"{tag.name} (error: {str(e)})")

            if added:
                changes_log.append(
                    f"- {forum.name}: would add {len(added)} tag(s) ({', '.join(added)})"
                    if dry_run else
                    f"- {forum.name}: added {len(added)} tag(s) ({', '.join(added)})"
                )
            else:
                changes_log.append(f"- {forum.name}: no changes")

        output = f"✅ {'Dry run of' if dry_run else ''} Tag sync complete!\n\nChanges:\n" + "\n".join(
            changes_log)
        await send_chunks(ctx, output)

    @commands.command()
    async def syncdesc(self, ctx, origin_name: str, target_name: str, *, mode: str = ""):
        """Sync forum description from one forum to another."""
        dry_run = mode.lower() == "dry"
        changes_log = []

        origin_forum = discord.utils.get(ctx.guild.channels,
                                         name=origin_name,
                                         type=discord.ChannelType.forum)
        target_forum = discord.utils.get(ctx.guild.channels,
                                         name=target_name,
                                         type=discord.ChannelType.forum)

        if not origin_forum or not target_forum:
            await ctx.send(
                f"Could not find one or both forum channels: `{origin_name}`, `{target_name}`."
            )
            return

        origin_desc = origin_forum.topic or ""
        target_desc = target_forum.topic or ""

        if origin_desc.strip() == target_desc.strip():
            await ctx.send(
                f"- {target_name}: no changes (description already matches)")
            return

        if dry_run:
            changes_log.append(f"- {target_name}: would update description (dry)")
        else:
            try:
                await target_forum.edit(topic=origin_desc)
                changes_log.append(f"- {target_name}: updated description")
            except Exception as e:
                changes_log.append(
                    f"- {target_name}: error updating description ({str(e)})")

        await ctx.send("\n".join(changes_log))


    @commands.command()
    async def syncalldesc(self, ctx, origin_name: str, *args):
        """Sync forum description from one forum to all forums in a category."""
        if not args:
            await ctx.send("Please specify a target category name.")
            return

        dry_run = args[-1].lower() == "dry"
        if dry_run:
            target_category_name = " ".join(args[:-1])
        else:
            target_category_name = " ".join(args)

        changes_log = []

        origin_forum = discord.utils.get(ctx.guild.channels,
                                         name=origin_name,
                                         type=discord.ChannelType.forum)
        if not origin_forum:
            await ctx.send(f"Source forum channel '{origin_name}' not found.")
            return

        origin_desc = origin_forum.topic or ""

        target_forums = [
            ch for ch in ctx.guild.channels if ch.type == discord.ChannelType.forum
            and ch.category and ch.category.name == target_category_name
        ]

        if not target_forums:
            await ctx.send(
                f"No forum channels found in category '{target_category_name}'.")
            return

        for forum in target_forums:
            target_desc = forum.topic or ""
            if origin_desc.strip() == target_desc.strip():
                changes_log.append(f"- {forum.name}: no changes")
                continue

            if dry_run:
                changes_log.append(
                    f"- {forum.name}: would update description (dry)")
            else:
                try:
                    await forum.edit(topic=origin_desc)
                    changes_log.append(f"- {forum.name}: updated description")
                    await asyncio.sleep(0.5)  # <-- delay added here
                except Exception as e:
                    changes_log.append(
                        f"- {forum.name}: error updating description ({str(e)})")

        output = f"✅ {'Dry run of' if dry_run else ''} Description sync complete!\n\nChanges:\n" + "\n".join(
            changes_log)
        await send_chunks(ctx, output)
    @commands.command()
    async def listforums(self, ctx):
        # Filter for forum channels from the guild's channels
        forum_channels = [ch for ch in ctx.guild.channels if ch.type == discord.ChannelType.forum]

        if forum_channels:
            # Create a dictionary to group forums by their category name
            categories = {}
            for ch in forum_channels:
                # Use "No Category" for channels without a category
                category_name = ch.category.name if ch.category else "No Category"
                categories.setdefault(category_name, []).append(ch.name)

            # Build the message by sorting categories and their forum names alphabetically
            message = "Found forum channels:\n"
            for category in sorted(categories.keys()):
                message += f"\n**{category}**:\n"
                for forum in sorted(categories[category]):
                    message += f"- {forum}\n"

            await send_chunks(ctx, message)
        else:
            await ctx.send("No forum channels found.")
    

async def setup(bot):
    await bot.add_cog(SyncCog(bot))