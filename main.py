import discord
from sys import argv
from dotenv import load_dotenv
from os import getenv

dev = len(argv) >= 2 and argv[1] == "dev"

load_dotenv()
token = getenv("TOKEN_ALPHA" if dev else "TOKEN")

bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"{bot.user} 온라인!")

bot.run(token)
