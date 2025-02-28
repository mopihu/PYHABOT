import argparse
import logging
from functools import partial

from .config_handler import DefaultConfig

# fmt: off
COMMANDS = [
    {"command": "help",            "arguments": [],                          "help": "Listázza az elérhető parancsokat."},
    {"command": "add",             "arguments": [("url", str)],              "help": "Felvesz egy új hirdetésfigyelőt."},
    {"command": "remove",          "arguments": [("watch_id", int)],               "help": "Töröl egy létező hirdetésfigyelőt."},
    {"command": "list",            "arguments": [],                          "help": "Listázza a felvett hirdetésfigyelőket."},
    {"command": "info",            "arguments": [("watch_id", int)],               "help": "Lekéri egy hirdetésfigyelő adatait."},
    {"command": "seturl",          "arguments": [("watch_id", int), ("url", str)], "help": "Módosítja egy hirdetésfigyelő URL-jét."},
    {"command": "notifyon",        "arguments": [("watch_id", int)],               "help": "Beállítja a jelenlegi chat-et az értesítések megjelenítésehez."},
    {"command": "setwebhook",      "arguments": [("watch_id", int), ("url", str)], "help": "Beállítja a webhookot egy hirdetésfigyelőhöz."},
    {"command": "unsetwebhook",    "arguments": [("watch_id", int)],               "help": "Kitörli a webhookot egy hirdetésfigyelőtől."},
    {"command": "rescrape",        "arguments": [("watch_id", int, "?")],          "help": "Törli a mentett hirdetéseket és újra lekéri azokat."},
    {"command": "listads",         "arguments": [("watch_id", int)],               "help": "Lekéri az hirdetésfigyelőhöz tarozó hirdetéseket."},
    {"command": "adinfo",          "arguments": [("ad_id", int)],               "help": "Lekéri a hirdetés adatait."},
    {"command": "setpricealert",   "arguments": [("ad_id", int)],               "help": "Beállít árváltozás értesítőt egy hirtetéshez."},
    {"command": "unsetpricealert", "arguments": [("ad_id", int)],               "help": "Beállít árváltozás értesítőt egy hirtetéshez."},
    {"command": "settings",        "arguments": [],                          "help": "Lekéri a bot beállításait."},
    {"command": "setprefix",       "arguments": [("prefix", str)],           "help": "Módosítja a parancs prefixumot."},
    {"command": "setinterval",     "arguments": [("interval", int)],         "help": "Beállítja a frissítés gyakoriságát másodpercekben."},
]
# fmt: on

logger = logging.getLogger("pyhabot_logger")


def dummy_callback(cbname="", *args, **kwargs):
    raise NotImplementedError(f"You forgot to register a callback for [{cbname}]")


def error(message):
    raise ValueError(message)


class CommandHandler:
    def __init__(self):
        self.prefix = DefaultConfig.COMMANDS_PREFIX
        self.parser = argparse.ArgumentParser(add_help=False)  # Disable default --help
        self.parser.error = error
        subparsers = self.parser.add_subparsers(dest="command")
        self.subparsers: dict[str, argparse.ArgumentParser] = {}
        for cmd in COMMANDS:
            sp = subparsers.add_parser(cmd["command"], help=cmd["help"], add_help=False)
            sp.set_defaults(func=partial(dummy_callback, cmd["command"]))
            sp.error = error
            for arg in cmd["arguments"]:
                sp.add_argument(arg[0], type=arg[1], nargs=arg[2] if len(arg) > 2 else None)
            self.subparsers[cmd["command"]] = sp

    def register_callback(self, cmd, callback):
        self.subparsers[cmd["command"]].set_defaults(func=callback)

    def handle(self, args):
        if args and args[0].startswith(self.prefix):
            args[0] = args[0][len(self.prefix) :]
            args = self.parser.parse_args(args)
            logger.debug(args)
            return partial(
                args.func, **{key: value for key, value in vars(args).items() if key not in ("command", "func")}
            )

    def help(self):
        text = "Elérhető parancsok:"
        for cmd in COMMANDS:
            cmd_args = self.prefix + cmd["command"] + " " + (" ".join(f"<{arg[0]}>" for arg in cmd["arguments"]))
            text += f'\n  {cmd_args:<25} | {cmd["help"]}'
        return text
