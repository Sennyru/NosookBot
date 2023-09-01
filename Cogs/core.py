import discord
from discord.ext import commands
from datetime import datetime
from traceback import format_exc
from nosookbot import NosookBot


class Core(commands.Cog):
    def __init__(self, bot: NosookBot):
        self.bot = bot
        self.log_channel: discord.TextChannel = None
    
    
    @commands.Cog.listener()
    async def on_ready(self):
        log_channel_id = 1138430000442384454
        self.log_channel = self.bot.get_channel(log_channel_id) or await self.bot.fetch_channel(log_channel_id)
        
        await self.bot.change_presence(activity=discord.Game(name="노숙"))
        
        guild_count = len(self.bot.guilds)
        NosookBot.log(f"{self.bot.user.display_name} 온라인! (서버 {guild_count}개)")
        await self.log_channel.send(f"온라인! (서버 {guild_count}개)")
    
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        NosookBot.log(f"{guild.name}({guild.id}) 서버에 초대됨")
        await self.log_channel.send(f"{self.owner_mention} `{guild.name}({guild.id})` 서버에 초대되었습니다!!!!")
    
    
    @commands.Cog.listener()
    async def on_application_command(self, ctx: discord.ApplicationContext):
        NosookBot.log(f"{ctx.user.name}({ctx.user.id})(이)가 /{ctx.command.name} 사용")
    
    
    @commands.slash_command(name="노숙봇", description="봇 정보를 표시합니다.")
    async def slash_info(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(title="🟢 노숙봇", description=NosookBot.github, color=NosookBot.color)
        embed.add_field(name="v0.6.1", value="""
        * 1시간마다 타임라인 새로고침 중 오류가 발생할 경우 새로고침 task가 아예 중지되는 현상 수정
                                                     """, inline=False)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Made by {self.bot.get_user(self.bot.owner_ids[0]).display_name}",
                         icon_url=self.bot.get_user(self.bot.owner_ids[0]).avatar.url)
        await ctx.respond(embed=embed)
    
    
    @commands.slash_command(name="리로드", description="Cogs를 새로고침합니다.", guild_ids=[1135172384152891453, 741194068939243531])
    @commands.is_owner()
    async def slash_reload(self, ctx: discord.ApplicationContext):
        NosookBot.log("리로드 중")
        for cog in NosookBot.cogs:
            self.bot.reload_extension(cog)
        NosookBot.log("리로드 완료")
        await ctx.respond("🔄 봇을 리로드하였습니다.", ephemeral=True)
    
    
    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.errors.MissingPermissions):
            await ctx.respond(f"`{', '.join(error.missing_permissions)}` 권한이 필요합니다.", ephemeral=True)
            return
        
        embed = discord.Embed(title="❌ 오류가 발생했습니다.", description=f"```py\n{error}```", color=0xff0000)
        embed.set_footer(text=f"디스코드 {self.bot.get_user(self.bot.owner_ids[0]).display_name}(으)로 문의해주세요.",
                         icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = datetime.now(NosookBot.timezone)
        await ctx.respond(embed=embed, ephemeral=True)
        
        await self.log_channel.send(f"{self.owner_mention} `/{ctx.command.name}` 실행 오류! 당장 로그를 확인하세요!")
        NosookBot.log(f"/{ctx.command.name} 실행 오류! 아래 예외를 확인하세요.")
        print(format_exc())
    


@NosookBot.cog_logger
def setup(bot: NosookBot):
    bot.add_cog(Core(bot))
