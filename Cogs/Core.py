import discord
from discord.ext import commands
from utility import log


class Core(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        log(f"{self.bot.user} 온라인!")
    

def setup(bot: discord.Bot):
    bot.add_cog(Core(bot))
