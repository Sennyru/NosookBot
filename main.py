import discord
from sys import argv
from dotenv import load_dotenv
from os import environ
from nosookbot import NosookBot
from modules.general import general
from modules.call_log import call_log

NosookBot.log("로딩...")

is_alpha_channel = len(argv) >= 2 and argv[1] == "alpha"

load_dotenv()
token = environ["TOKEN" if not is_alpha_channel else "TOKEN_ALPHA"]

cog_names = [general.__name__, call_log.__name__]
owner_ids = [540481950763319317, 718285849888030720]
bot = NosookBot(is_alpha_channel, cog_names, owner_ids=owner_ids, intents=discord.Intents.all())

bot.run(token)
