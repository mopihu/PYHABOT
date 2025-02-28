import logging

import discord

from .integration_base import IntegrationBase, MessageBase


logger = logging.getLogger("pyhabot_logger")


class DiscordMessage(MessageBase):
    def __init__(self, msg):
        self._msg: discord.Message = msg

    @property
    def text(self):
        return self._msg.content

    @property
    def channel_id(self):
        return self._msg.channel.id

    async def send_back(self, text, no_preview=False, **kwargs):
        message = await self._msg.channel.send(text)
        await message.edit(suppress=no_preview)
        return message

    async def reply(self, text):
        return self._msg.reply(text)


class DiscordIntegration(discord.Client, IntegrationBase):
    def __init__(self, token):
        intents = discord.Intents.default()
        intents.message_content = True
        discord.Client.__init__(self, intents=intents)
        IntegrationBase.__init__(self, token)

    async def on_message(self, message: discord.Message):
        if not message.author.bot:
            await self.on_message_callback(DiscordMessage(message))

    async def on_ready(self):
        await self.on_ready_callback()  # propagate event to PyHabot
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="HardverApró"))
        logger.info(
            f"Invite link: https://discord.com/oauth2/authorize?client_id={self.user.id}&scope=bot&permissions=8"
        )

    def run(self):
        return discord.Client.run(self, self.token)

    async def send_message_to_channel(self, channel_id, text, no_preview=False, **kwargs):
        channel = self.get_channel(channel_id)
        if channel:
            for chunk in DiscordMessage.split_to_chunks(text):
                message = await channel.send(chunk)
                await message.edit(suppress=no_preview)
