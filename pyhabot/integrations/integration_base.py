from abc import ABC, abstractmethod
import logging


logger = logging.getLogger("pyhabot_logger")


class classproperty:
    def __init__(self, func):
        self.fget = func

    def __get__(self, instance, owner):
        return self.fget(owner)


class MessageBase(ABC):
    @property
    @abstractmethod
    def text(self):
        pass

    @property
    @abstractmethod
    def channel_id(self):
        pass

    @abstractmethod
    async def send_back(self, text, no_preview=False, **kwargs):
        pass

    @abstractmethod
    async def reply(self, text):
        pass

    @staticmethod
    def split_to_chunks(text, size=2000):
        return (text[i : i + size] for i in range(0, len(text), size))

    @staticmethod
    def format_hyperlink(text, url):
        return f"[{text}]({url})"

    @staticmethod
    def escape(text):
        return text

    @staticmethod
    def strikethrough(text):
        return f"~~{text}~~"


class IntegrationBase(ABC):
    def __init__(self, token):
        self.token = token
        self.on_message_callback = lambda *_: None
        self.on_ready_callback = lambda *_: None
        logger.info(f"Started with '{self.name}'!")

    def register_on_message_callback(self, callback):
        self.on_message_callback = callback

    def register_on_ready_callback(self, callback):
        self.on_ready_callback = callback

    @classproperty
    def name(cls):
        return cls.__name__

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    async def send_message_to_channel(self, channel_id, text, no_preview=False, **kwargs):
        pass
