import logging

import discord
from redbot.core import checks, commands
from redbot.core.bot import Red

SUPPORT_CHANNEL_ID = 444660866273771540
PUNISH_REACTION = "\N{BIOHAZARD SIGN}"
OWNER_IDS = (78631113035100160, 240961564503441410)
BOT_ID = 275047522026913793

PUNISH_PERMS = 329792

log = logging.getLogger("red.sinbadcogs.support")

COMMIT_FIX = """
The following is a single command that will fix the whole problem in theory
With that said, running evals is dangerous, as is touching things owned by other cogs.

Use this only if you are confident in understanding what this is doing.
This should only be run on Red Version 3.3.10 (where it was tested):

This will fix the data red has stored about a fork, update, and reload.

[p]eval
```py
ctx.assume_yes = True
downloader = bot.get_cog("Downloader")
installed_cogs = await downloader.installed_cogs()
updated_cogs = []
for cog in installed_cogs:
    if cog.repo and cog.repo.url == "https://github.com/mikeshardmind/SinbadCogs":
        cog.commit = ""
        updated_cogs.append(cog)
await downloader._save_to_installed(updated_cogs)
await ctx.invoke(bot.get_command("cog update"), *updated_cogs)
```
"""

MESSAGE_ALT = (
    "https://discordapp.com/channels/"
    "240154543684321280/444660866273771540/734090016740999218"
)


class Support(commands.Cog, name="Sinbad's Support Toolbox"):
    """
    Shhhhhhh.
    """

    async def red_delete_data_for_user(self, **kwargs):
        """ Nothing to delete """
        return

    def __init__(self, bot: Red):
        self.bot: Red = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if (
            message.author.id in (BOT_ID, *OWNER_IDS)
            or message.channel.id != SUPPORT_CHANNEL_ID
        ):
            return

        await self.maybe_notify_against_mentioning(message)

        await self.maybe_delete_for_attach(message)

    async def safe_send(self, channel_id: int, text: str):
        r = discord.http.Route(
            "POST", "/channels/{channel_id}/messages", channel_id=channel_id,
        )
        kwargs = {
            "allowed_mentions": {"parse": []},
            "content": text,
        }

        await self.bot.http.request(r, json=kwargs)  # type: ignore

    async def maybe_delete_for_attach(self, message: discord.Message):

        if not message.attachments:
            return

        elif sum(a.size for a in message.attachments) > 8_000_000:
            try:
                await message.delete()
            except discord.HTTPException as exc:
                log.exception("Delete fail", exc_info=exc)

            await self.safe_send(
                message.channel.id,
                f"Please refrain from large attachments. "
                f"{message.author.mention} ({message.author})",
            )
            return

        elif message.attachments[0].filename == "message.txt":

            try:
                await message.delete()
            except discord.HTTPException as exc:
                log.exception("Delete fail", exc_info=exc)

            await self.safe_send(
                message.channel.id,
                f"Please use <https://gist.github.com> or <https://mystb.in/> "
                f"for content which will not fit in a single message "
                f"{message.author.mention} ({message.author})",
            )
            return

        if not all((a.height and a.width) for a in message.attachments):

            await self.safe_send(
                message.channel.id,
                "This message appears to have a non-mobile friendly attachment. "
                "If this is the case (detection is experimental) "
                "you may want to consider sending this another way."
                f"{message.author.mention} ({message.author})",
            )

    async def maybe_notify_against_mentioning(self, message: discord.Message):

        for u in message.mentions:
            if u.id in OWNER_IDS:

                await self.safe_send(
                    message.channel.id,
                    f"Please refrain from mentioning. "
                    f"{message.author.mention} ({message.author})",
                )

    async def get_message(self, channel: discord.TextChannel, _id: int):

        message = next(filter(lambda m: m.id == _id, self.bot.cached_messages), None)
        if message:
            return message
        try:
            message = await channel.fetch_message(_id)
        except discord.HTTPException:
            return None
        else:
            return message

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):

        if not payload.channel_id == SUPPORT_CHANNEL_ID:
            return
        if payload.user_id not in OWNER_IDS:
            return
        if PUNISH_REACTION not in str(payload.emoji):
            return

        if not (channel := self.bot.get_channel(SUPPORT_CHANNEL_ID)):
            return

        assert isinstance(channel, discord.TextChannel)  # nosec
        message = await self.get_message(channel, payload.message_id)
        if not message:
            return

        author = message.author
        if author.id in (BOT_ID, *OWNER_IDS):
            return
        if channel.permissions_for(author).value & PUNISH_PERMS:
            overwrites = channel.overwrites

            auth_overwrites = overwrites.get(author, None)
            if auth_overwrites is None:
                auth_overwrites = discord.PermissionOverwrite()

            allow, deny = auth_overwrites.pair()
            allow.value = allow.value & ~PUNISH_PERMS
            deny.value = deny.value | PUNISH_PERMS
            auth_overwrites = discord.PermissionOverwrite.from_pair(allow, deny)

            await channel.set_permissions(
                author, overwrite=auth_overwrites, reason="Emoji Mute."
            )

    @checks.is_owner()
    @commands.command()
    async def fixswitch(self, ctx, confident: bool = False):
        if not confident:
            await ctx.send(f"Follow the directions in this link: <{MESSAGE_ALT}>")
        else:
            await ctx.send(COMMIT_FIX)
