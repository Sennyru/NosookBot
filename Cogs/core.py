import discord
from discord.ext import commands
from datetime import datetime
from nosookbot import NosookBot


class Core(commands.Cog):
    def __init__(self, bot: NosookBot):
        self.bot = bot
        self.log_channel: discord.TextChannel = None
        self.owner_mention: str = None
    
    
    @commands.Cog.listener()
    async def on_ready(self):
        log_channel_id = 1138430000442384454
        self.log_channel = self.bot.get_channel(log_channel_id) or await self.bot.fetch_channel(log_channel_id)
        self.owner_mention = self.bot.get_user(self.bot.owner_ids[0]).mention
        
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
        embed = discord.Embed(title="🟢 노숙봇", description="https://github.com/Secon0101/NosookBot", color=0x78b159)
        embed.add_field(name="v0.5.3", value="""
* 타임라인에 색깔 안내 추가
            """, inline=False)
        embed.add_field(name="v0.5.2", value="""
* 메시지 및 채널 탐색 코드 보완
            """, inline=False)
        embed.add_field(name="v0.5.1", value="""
* 서버 아이콘이 없으면 타임라인이 생성되지 않는 버그 수정
            """, inline=False)
        embed.add_field(name="v0.5", value="""
* 리얼타임 채널 메시지 삭제 대기 시간 5분에서 60분으로 변경
            """, inline=False)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Made by {self.bot.get_user(self.bot.owner_ids[0]).display_name}",
                         icon_url=self.bot.get_user(self.bot.owner_ids[0]).avatar.url)
        await ctx.respond(embed=embed)
    
    
    @commands.slash_command(name="리로드", description="Cogs를 새로고침합니다.", guild_ids=[1135172384152891453, 741194068939243531])
    @commands.is_owner()
    async def slash_reload(self, ctx: discord.ApplicationContext):
        NosookBot.log("리로드 중")
        for cog in NosookBot.get_cogs():
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
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
        raise error
    


@NosookBot.cog_logger
def setup(bot: NosookBot):
    bot.add_cog(Core(bot))
