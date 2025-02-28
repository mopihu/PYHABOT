import json
from pathlib import Path


CONFIG_FILENAME = "config.json"


class DefaultConfig:
    COMMANDS_PREFIX = "!"
    REFRESH_INTERVAL = 60


class ConfigHandler:
    def __init__(self, folder: Path | str, filename: str = CONFIG_FILENAME):
        self._commands_prefix: str = DefaultConfig.COMMANDS_PREFIX
        self._refresh_interval: int = DefaultConfig.REFRESH_INTERVAL

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

        if failed:
            self._save()

    def _dump(self):
        return {
            "commands_prefix": self.commands_prefix,
            "refresh_interval": self.refresh_interval,
        }
