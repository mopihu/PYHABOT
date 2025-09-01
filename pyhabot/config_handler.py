import json
from pathlib import Path


CONFIG_FILENAME = "config.json"


class DefaultConfig:
    COMMANDS_PREFIX = "!"
    REFRESH_INTERVAL = 60
    REQUEST_DELAY_MIN = 1
    REQUEST_DELAY_MAX = 5
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
    ]
    INTERVAL_JITTER_PERCENT = 10
    MAX_RETRIES = 5
    RETRY_BASE_DELAY = 10


class ConfigHandler:
    def __init__(self, folder: Path | str, filename: str = CONFIG_FILENAME):
        self._commands_prefix: str = DefaultConfig.COMMANDS_PREFIX
        self._refresh_interval: int = DefaultConfig.REFRESH_INTERVAL
        self._request_delay_min: int = DefaultConfig.REQUEST_DELAY_MIN
        self._request_delay_max: int = DefaultConfig.REQUEST_DELAY_MAX
        self._user_agents: list = DefaultConfig.USER_AGENTS.copy()
        self._interval_jitter_percent: int = DefaultConfig.INTERVAL_JITTER_PERCENT
        self._max_retries: int = DefaultConfig.MAX_RETRIES
        self._retry_base_delay: int = DefaultConfig.RETRY_BASE_DELAY

        folder = Path(folder)
        folder.mkdir(exist_ok=True)
        self._file = folder / filename
        try:
            with open(self._file) as f:
                self._load(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            self._save()

    @property
    def commands_prefix(self) -> str:
        return self._commands_prefix

    @commands_prefix.setter
    def commands_prefix(self, value):
        self._commands_prefix = value
        self._save()

    @property
    def refresh_interval(self) -> int:
        return self._refresh_interval

    @refresh_interval.setter
    def refresh_interval(self, value):
        self._refresh_interval = value
        self._save()

    @property
    def request_delay_min(self) -> int:
        return self._request_delay_min

    @request_delay_min.setter
    def request_delay_min(self, value):
        self._request_delay_min = value
        self._save()

    @property
    def request_delay_max(self) -> int:
        return self._request_delay_max

    @request_delay_max.setter
    def request_delay_max(self, value):
        self._request_delay_max = value
        self._save()

    @property
    def user_agents(self) -> list:
        return self._user_agents

    @user_agents.setter
    def user_agents(self, value):
        self._user_agents = value
        self._save()

    @property
    def interval_jitter_percent(self) -> int:
        return self._interval_jitter_percent

    @interval_jitter_percent.setter
    def interval_jitter_percent(self, value):
        self._interval_jitter_percent = value
        self._save()

    @property
    def max_retries(self) -> int:
        return self._max_retries

    @max_retries.setter
    def max_retries(self, value):
        self._max_retries = value
        self._save()

    @property
    def retry_base_delay(self) -> int:
        return self._retry_base_delay

    @retry_base_delay.setter
    def retry_base_delay(self, value):
        self._retry_base_delay = value
        self._save()

    def _save(self):
        with open(self._file, "w") as f:
            json.dump(self._dump(), f, indent=4, sort_keys=True)

    def _load(self, data):
        failed = False
        try:
            self._commands_prefix = data["commands_prefix"]
        except KeyError:
            self._commands_prefix = DefaultConfig.COMMANDS_PREFIX
            failed = True

        try:
            self._refresh_interval = data["refresh_interval"]
        except KeyError:
            self._refresh_interval = DefaultConfig.REFRESH_INTERVAL
            failed = True

        try:
            self._request_delay_min = data["request_delay_min"]
        except KeyError:
            self._request_delay_min = DefaultConfig.REQUEST_DELAY_MIN
            failed = True

        try:
            self._request_delay_max = data["request_delay_max"]
        except KeyError:
            self._request_delay_max = DefaultConfig.REQUEST_DELAY_MAX
            failed = True

        try:
            self._user_agents = data["user_agents"]
        except KeyError:
            self._user_agents = DefaultConfig.USER_AGENTS.copy()
            failed = True

        try:
            self._interval_jitter_percent = data["interval_jitter_percent"]
        except KeyError:
            self._interval_jitter_percent = DefaultConfig.INTERVAL_JITTER_PERCENT
            failed = True

        try:
            self._max_retries = data["max_retries"]
        except KeyError:
            self._max_retries = DefaultConfig.MAX_RETRIES
            failed = True

        try:
            self._retry_base_delay = data["retry_base_delay"]
        except KeyError:
            self._retry_base_delay = DefaultConfig.RETRY_BASE_DELAY
            failed = True

        if failed:
            self._save()

    def _dump(self):
        return {
            "commands_prefix": self.commands_prefix,
            "refresh_interval": self.refresh_interval,
            "request_delay_min": self.request_delay_min,
            "request_delay_max": self.request_delay_max,
            "user_agents": self.user_agents,
            "interval_jitter_percent": self.interval_jitter_percent,
            "max_retries": self.max_retries,
            "retry_base_delay": self.retry_base_delay,
        }
