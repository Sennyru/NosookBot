import discord
from discord.ext import commands
from os import getenv
from os.path import exists
from base64 import b64decode
import firebase_admin as firebase
from firebase_admin import db
from datetime import datetime
from pytz import timezone
from utility import log, cog_logger


class CallLog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        
        # 파이어베이스
        if firebase._apps:
            log("이미 파이어베이스에 연결됨")
            return
        
        log("파이어베이스 연결 중...")
        fb_admin = "firebase-admin.json"
        
        # 파일이 없거나 비어 있으면 생성
        need_to_create = False
        if not exists(fb_admin):
            need_to_create = True
            log(f"{fb_admin} 파일 없음. 생성 중...")
        else:
            with open(fb_admin, 'r') as f:
                if not f.read():
                    need_to_create = True
                    log(f"{fb_admin} 파일 비어있음. 생성 중...")
        if need_to_create:
            with open(fb_admin, 'w') as f:
                f.write(b64decode(getenv("FIREBASE_ADMIN_BASE64")).decode("utf-8"))
            log(f"{fb_admin} 생성 완료")
        
        cred = firebase.credentials.Certificate("firebase-admin.json")
        firebase.initialize_app(cred, {"databaseURL": getenv("DATABASE_URL")})
        log("파이어베이스 로드 완료")
    
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member,
                                    before: discord.VoiceState, after: discord.VoiceState):
        # on join
        if before.channel is None and after.channel is not None:
            await self.update_call_log(member.id, 1, after.channel)
        
        # on leave
        elif before.channel is not None and after.channel is None:
            await self.update_call_log(member.id, 0, before.channel)
    
    
    async def update_call_log(self, member_id: int, status: int, channel: discord.VoiceChannel):
        """ 통화 기록을 데이터베이스에 저장하고, 실시간 타임라인 임베드를 업데이트한다. """
        
        # 실시간 타임라인 업데이트
        ref = db.reference(f"realtime_channel/{channel.guild.id}")
        realtime_data: dict[str, int] = ref.get()
        if realtime_data is None:
            return
        
        message = self.bot.get_message(realtime_data["message"])
        if message is None:
            ref.delete()
            await self.bot.get_channel(realtime_data["channel"]).send("타임라인 메시지를 찾을 수 없습니다. 채널을 다시 설정해주세요.")
            return
        
        await message.edit(embed=CallLog.make_timeline_embed())
    
    
    @staticmethod
    def make_timeline_embed() -> discord.Embed:
        """ 실시간 타임라인 임베드를 생성한다. """
        embed = discord.Embed(title="📜 실시간 타임라인", color=0x78b159)
        embed.timestamp = datetime.now(timezone('Asia/Seoul'))
        return embed
    
    
    @commands.has_permissions(manage_channels=True)
    @commands.slash_command(name="리얼타임", description="해당 채널을 실시간 타임라인이 뜨는 채널로 설정합니다.")
    async def slash_set_realtime_channel(self, ctx: discord.ApplicationContext):
        channel = db.reference(f"realtime_channel/{ctx.guild.id}/channel").get()
        if channel == ctx.channel.id:
            await ctx.respond("이미 실시간 타임라인 채널로 설정되어 있습니다.", ephemeral=True)
            return
        
        class Button(discord.ui.View):
            @discord.ui.button(label="예", style=discord.ButtonStyle.green)
            async def button_yes(self, button: discord.ui.Button, interaction: discord.Interaction):
                timeline = await interaction.channel.send(embed=CallLog.make_timeline_embed())
                db.reference(f"realtime_channel/{ctx.guild.id}").update({
                    "channel": ctx.channel.id,
                    "message": timeline.id
                })
                await confirm.edit_original_response(content="채널을 **실시간 타임라인 채널**로 설정했습니다!", view=None)
            
            @discord.ui.button(label="아니요", style=discord.ButtonStyle.red)
            async def button_no(self, button: discord.ui.Button, interaction: discord.Interaction):
                await confirm.edit_original_response(content="실시간 타임라인 채널 등록을 취소하였습니다.", view=None)
        
        confirm = await ctx.respond("이 채널을 **실시간 타임라인 채널**로 설정할까요?", view=Button(), ephemeral=True)
        
    


@cog_logger
def setup(bot: discord.Bot):
    bot.add_cog(CallLog(bot))
