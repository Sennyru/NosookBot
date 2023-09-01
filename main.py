import discord
from sys import argv
from dotenv import load_dotenv
from os import getenv
from nosookbot import NosookBot

NosookBot.log("로딩...")

dev = len(argv) >= 2 and argv[1] == "dev"

load_dotenv()
token = getenv("TOKEN" if not dev else "TOKEN_ALPHA")

bot = NosookBot(dev, owner_ids=[540481950763319317, 718285849888030720], intents=discord.Intents.all())

bot.run(token)
