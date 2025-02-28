import re
import asyncio

from telegrampy.ext.commands import Bot as TelegramBot
import telegrampy

from .integration_base import IntegrationBase, MessageBase


class TelegramMessage(MessageBase):
    def __init__(self, msg):
        self._msg: telegrampy.Message = msg

    @property
    def text(self):
        return self._msg.content

    @property
    def channel_id(self):
        return self._msg.chat.id

    async def send_back(self, text, no_preview=False, **kwargs):
        params = {"chat_id": self._msg.chat.id, "parse_mode": "Markdown", **kwargs}
        if no_preview:
            params["disable_web_page_preview"] = True

        for chunk in self.split_to_chunks(text):
            params["text"] = chunk
            await self._msg._http.request("sendMessage", json=params)

    async def reply(self, text, **kwargs):
        for chunk in self.split_to_chunks(text):
            await self._msg.reply(chunk, parse_mode="Markdown")

    @staticmethod
    def split_to_chunks(text, size=4000):
        # return MessageBase.split_to_chunks(TelegramMessage.escape(text), size)
        return MessageBase.split_to_chunks(text, size)

    @staticmethod
    def escape(text: str):
        _special_chars_map = {i: "\\" + chr(i) for i in b"_"}

        # Regex pattern to find inline (`code`) and multiline (```code```) code blocks
        pattern = r"(```.*?```|`[^`\n]*`)"

        # List to store parts of the final result
        parts = []
        last_end = 0

        # Iterate through all code blocks
        for match in re.finditer(pattern, text, re.DOTALL):  # re.DOTALL ensures multiline ` ``` ` is matched
            start, end = match.span()
            # Escape text outside code blocks
            parts.append(text[last_end:start].translate(_special_chars_map))
            # Keep the code block unchanged
            parts.append(text[start:end])
            last_end = end

        # Add remaining text after the last code block
        parts.append(text[last_end:].translate(_special_chars_map))

        return "".join(parts)


class TelegramIntegration(TelegramBot, IntegrationBase):
    def __init__(self, token):
        TelegramBot.__init__(self, token)
        IntegrationBase.__init__(self, token)
        self.event(self.on_message)

    def run(self):
        asyncio.get_event_loop().create_task(self.on_ready_callback())
        super().run()

    async def on_message(self, message):
        await self.on_message_callback(TelegramMessage(message))

    async def send_message_to_channel(self, channel_id, text, no_preview=False, **kwargs):
        chat = await self.get_chat(channel_id)
        params = {"chat_id": chat.id, "parse_mode": "Markdown", **kwargs}
        if no_preview:
            params["disable_web_page_preview"] = True

        for chunk in TelegramMessage.split_to_chunks(text):
            params["text"] = chunk
            await self.http.request("sendMessage", json=params)
