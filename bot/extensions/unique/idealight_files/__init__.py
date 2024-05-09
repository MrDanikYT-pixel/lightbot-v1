import lightbulb
import importlib


extensions = ['activity']


def load_all(bot: lightbulb.BotApp):
    for x in extensions:
        importlib.import_module(f".{x}", __package__).load(bot)


def unload_all(bot: lightbulb.BotApp):
    for x in extensions:
        importlib.import_module(f".{x}", __package__).unload(bot)
