import discord
from discord.ext import commands
from datetime import datetime
from pytz import timezone
from utility import log, get_cogs, cog_logger


class Core(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
    
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Game(name="노숙"))
        
        log(f"{self.bot.user.display_name} 온라인!")
        await self.bot.get_channel(1006937118796435486).send("온라인!")
    
    
    @commands.Cog.listener()
    async def on_application_command(self, ctx: discord.ApplicationContext):
        log(f"{ctx.author.name}({ctx.author.id})(이)가 /{ctx.command.name} 사용")
    
    
    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.errors.MissingPermissions):
            await ctx.respond(f"`{', '.join(error.missing_permissions)}` 권한이 필요합니다.", ephemeral=True)
            return
        
        embed = discord.Embed(title="❌ 오류가 발생했습니다.", description=f"```py\n{error}```", color=0xff0000)
        embed.set_footer(text=f"{self.bot.get_user(self.bot.owner_ids[0]).display_name}(으)로 문의해주세요.",
                         icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = datetime.now(timezone('Asia/Seoul'))
        await ctx.respond(embed=embed, view=None, ephemeral=True)
        raise error
    
    
    @commands.slash_command(name="노숙봇", description="봇 정보를 표시합니다.")
    async def slash_info(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(title="🟢 노숙봇", description="https://github.com/Secon0101/NosookBot", color=0x78b159)
        embed.add_field(name="v0.4-beta2", value="""
* 봇 실행 시 실시간 타임라인을 업데이트하고 채널 메시지를 삭제합니다.
* `/리얼타임` 사용 시 그 채널의 모든 메시지를 삭제하고, 메시지를 고정하고, 채널 설명을 바꿉니다.
* 실시간 타임라인 채널에 올라오는 메시지는 5분 뒤에 삭제됩니다.
* `/타임라인` 명령어에 시간 구간 매개변수를 사용할 수 있습니다. 그 시간 동안의 타임라인을 보여줍니다.
        """, inline=False)
        embed.add_field(name="v0.4-beta", value="""
* 전체 코드 리메이크!
* **`/리얼타임`** 명령어로 실시간 타임라인 채널 설정 가능. 이름 그대로 실시간으로 업데이트됩니다!
* **`/타임라인`** 명령어로 타임라인 확인 가능.
* 서버별로 다른 타임라인이 표시됩니다.
        """, inline=False)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Made by {self.bot.get_user(self.bot.owner_ids[0]).display_name}",
                         icon_url=self.bot.get_user(self.bot.owner_ids[0]).avatar.url)
        await ctx.respond(embed=embed)
    
    
    @commands.slash_command(name="리로드", description="Cogs를 새로고침합니다.", guild_ids=[741194068939243531])
    @commands.is_owner()
    async def slash_reload(self, ctx: discord.ApplicationContext):
        log("리로드 중")
        for cog in get_cogs():
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        log("리로드 완료")
        await ctx.respond("🔄 봇을 리로드하였습니다.", ephemeral=True)
    


@cog_logger
def setup(bot: discord.Bot):
    bot.add_cog(Core(bot))
