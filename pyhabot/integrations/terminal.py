import asyncio
from .integration_base import IntegrationBase, MessageBase
import logging
import sys


logger = logging.getLogger("pyhabot_logger")


class TerminalMessage(MessageBase):
    def __init__(self, msg):
        self._msg = msg

    @property
    def text(self):
        return self._msg

    @property
    def channel_id(self):
        return "terminal"

    async def send_back(self, text, no_preview=False, **kwargs):
        print(text)

    async def reply(self, text, **kwargs):
        print(text)


class TerminalIntegration(IntegrationBase):
    def __init__(self, token):
        IntegrationBase.__init__(self, token)

    def run(self):
        logger.setLevel(logging.ERROR)  # prevent spam
        print("Started with terminal integration! Type 'exit' to quit.")
        asyncio.get_event_loop().create_task(self.on_ready_callback())
        asyncio.get_event_loop().run_until_complete(self.listen_for_messages())

    async def listen_for_messages(self):
        while True:
            message = await self.ainput("Enter a message: ")
            if message.strip().lower() == "exit":
                break
            await self.on_message_callback(TerminalMessage(message))

    @staticmethod
    async def ainput(string: str) -> str:
        await asyncio.get_event_loop().run_in_executor(None, lambda s=string: sys.stdout.write(s + " "))
        return await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)

    async def send_message_to_channel(self, channel_id, text, no_preview=False, **kwargs):
        print(text)
