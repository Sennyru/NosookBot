import discord
from discord.ext import commands
from datetime import datetime
from traceback import format_exc
from nosookbot import NosookBot


class General(commands.Cog):
    def __init__(self, bot: NosookBot):
        self.bot = bot
        self.log_channel: discord.TextChannel = None
    
    
    async def send_to_log_channel(self, message: str):
        """ 로그 채널에 메시지 전송 """
        if not self.log_channel:
            log_channel_id = 1138430000442384454 if self.bot.release_channel == "release" else 1194318699633577994
            self.log_channel = self.bot.get_channel(log_channel_id) or await self.bot.fetch_channel(log_channel_id)
        
        await self.log_channel.send(message)
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Game(name="노숙"))
        
        guild_count = len(self.bot.guilds)
        NosookBot.log(f"{self.bot.user.display_name} 온라인! (서버 {guild_count}개)")
        await self.send_to_log_channel(f"온라인! (서버 {guild_count}개)")
    
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        NosookBot.log(f"{guild.name}({guild.id}) 서버에 초대됨")
        await self.send_to_log_channel(f"{self.bot.owner_mention} `{guild.name}({guild.id})` 서버에 초대되었습니다!!!!")
    
    
    @commands.Cog.listener()
    async def on_application_command(self, ctx: discord.ApplicationContext):
        NosookBot.log(f"{ctx.user.name}({ctx.user.id})(이)가 /{ctx.command.name} 사용")
    
    
    @commands.slash_command(name="노숙봇", description="봇 정보를 표시합니다.")
    async def slash_info(self, ctx: discord.ApplicationContext):
        # 업데이트 정보 읽기
        info_file_path = f"{__package__.replace('.', '/')}/update_info.md"
        with open(info_file_path, encoding="utf-8") as f:
            version = f.readline().rstrip()
            details = f.read().rstrip()
        
        owner = self.bot.get_user(self.bot.owner_ids[0])
        
        embed = discord.Embed(title="🟢 노숙봇", description=NosookBot.github, color=NosookBot.color)
        embed.add_field(name=version, value=details, inline=False)
        embed.set_thumbnail(url=self.bot.user.display_avatar)
        embed.set_footer(text=f"Made by {owner.display_name}", icon_url=owner.display_avatar)
        
        await ctx.respond(embed=embed)
    
    
    @commands.slash_command(name="리로드", description="Cogs를 새로고침합니다.", guild_ids=[1135172384152891453, 741194068939243531])
    @commands.is_owner()
    async def slash_reload(self, ctx: discord.ApplicationContext):
        NosookBot.log("Cogs 언로드 중...")
        for cog in self.bot.cog_names:
            self.bot.unload_extension(cog)
        NosookBot.log("Cogs 언로드 완료")
        
        NosookBot.log("Cogs 로드 중...")
        self.bot.load_extensions(*self.bot.cog_names)
        NosookBot.log("Cogs 로드 완료")
        
        await ctx.respond("🔄 봇을 리로드하였습니다.", ephemeral=True)
    
    
    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.errors.MissingPermissions):
            await ctx.respond(f"`{', '.join(error.missing_permissions)}` 권한이 필요합니다.", ephemeral=True)
            return
        
        name = self.bot.get_user(self.bot.owner_ids[0]).name
        embed = discord.Embed(title="❌ 오류가 발생했습니다.", description=f"디스코드 @{name}(으)로 문의해주세요.", color=0xff0000)
        embed.set_footer(icon_url=self.bot.user.display_avatar.url, text="NosookBot")
        embed.timestamp = datetime.now(NosookBot.timezone)
        await ctx.respond(embed=embed, ephemeral=True)
        
        await self.send_to_log_channel(f"{self.bot.owner_mention} `/{ctx.command.name}` 실행 오류! 당장 로그를 확인하세요!")
        NosookBot.log(f"/{ctx.command.name} 실행 오류! 아래 예외를 확인하세요.")
        print(error, format_exc(), sep='\n')
    


@NosookBot.cog_logger
def setup(bot: NosookBot):
    bot.add_cog(General(bot))
