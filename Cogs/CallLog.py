import discord
from discord.ext import commands, tasks
from enum import Enum
from os import getenv
from os.path import exists
from base64 import b64decode
import firebase_admin as firebase
from firebase_admin import db
from datetime import datetime
from pytz import timezone
from time import time
from utility import log, cog_logger


class Status(Enum):
    JOIN = 1
    LEAVE = 0


class CallLog(commands.Cog):
    
    CLOCK_ICONS = "🕧🕜🕝🕞🕟🕠🕡🕢🕣🕤🕥🕦🕧🕜🕝🕞🕟🕠🕡🕢🕣🕤🕥🕦"
    MSG_DELETE_DELAY_MIN = 60
    TIMEZONE = timezone("Asia/Seoul")
    
    
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
    async def on_ready(self):
        self.task_update_timeline_every_hour.start()
        
        # 실시간 타임라인 업데이트
        log("실시간 타임라인 채널 초기화 중...")
        realtime_data = db.reference("realtime_channel").get()
        for guild_id in realtime_data:
            try:
                guild = self.bot.get_guild(int(guild_id)) or await self.bot.fetch_guild(int(guild_id))
            except discord.errors.NotFound:
                log(f"서버 {guild_id}를 찾을 수 없습니다.")
            else:
                await self.update_realtime_timeline(guild)
                
                # 채팅 클리어
                channel_id = realtime_data[guild_id]["channel"]
                channel: discord.TextChannel = guild.get_channel(channel_id) or await guild.fetch_channel(channel_id)
                await CallLog.clear_other_messages(channel, realtime_data[guild_id]["message"])
                
                # TODO 0.4 -> 0.5 : 타임라인 메시지 삭제 시간 5분에서 60분으로 변경
                permissions = channel.permissions_for(channel.guild.me)
                if permissions.manage_channels:
                    await channel.edit(topic=f"타임라인 이외의 메시지는 {CallLog.MSG_DELETE_DELAY_MIN}분 뒤에 삭제됩니다.")
        
        log("초기화 완료")
    
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member,
                                    before: discord.VoiceState, after: discord.VoiceState):
        # on join
        if before.channel is None and after.channel is not None:
            await CallLog.update_call_log(member.id, Status.JOIN, after.channel)
            await self.update_realtime_timeline(after.channel.guild)
        
        # on leave
        elif before.channel is not None and after.channel is None:
            await CallLog.update_call_log(member.id, Status.LEAVE, before.channel)
            await self.update_realtime_timeline(before.channel.guild)
    
    
    @staticmethod
    async def update_call_log(user_id: int, status: Status, channel: discord.VoiceChannel):
        """ 통화 기록을 데이터베이스에 저장한다. """
        
        db.reference(f"call_log/{channel.guild.id}/{user_id}/{int(time())}").update({
            "status": status.value,
            "channel": channel.id,
        })
    
    
    async def update_realtime_timeline(self, guild: discord.Guild):
        """ 서버의 타임라인을 만들고 업데이트한다. """
        
        ref = db.reference(f"realtime_channel/{guild.id}")
        realtime_data: dict[str, int] = ref.get()
        if realtime_data is None:
            return
        
        realtime_channel = self.bot.get_channel(realtime_data["channel"])
        if realtime_channel is None:
            ref.delete()
            return
        
        message = await realtime_channel.fetch_message(realtime_data["message"])
        if message is None:
            ref.delete()
            await realtime_channel.send("타임라인 메시지를 찾을 수 없습니다. 채널을 다시 설정해주세요.")
            return
        
        if message.author == self.bot.user:
            await message.add_reaction("🔄")
            await message.edit(embed=await self.make_timeline_embed(guild))
            log(f"서버 {guild.id} 타임라인 업데이트됨")
            await message.remove_reaction("🔄", self.bot.user)
        else:
            log(f"서버 {guild.id} 타임라인 업데이트 실패. 메시지를 수정할 수 없습니다. 혹시 노숙봇이 아니신가요?")
    
    
    async def make_timeline_embed(self, guild: discord.Guild, time_span=12) -> discord.Embed:
        """ 실시간 타임라인 임베드를 생성한다. """
        
        INTERVAL = 60 * 60  # 1시간
        
        current = int(time())
        end = current - current % INTERVAL + INTERVAL  # 타임라인 오른쪽 끝 시각
        start = end - time_span * INTERVAL  # 타임라인 왼쪽 끝 시각
        call_log: dict = db.reference(f"call_log/{guild.id}").get() or {}
        timeline: dict = {}  # 멤버별 타임라인 저장
        
        # 타임라인 생성
        for member_id, member_logs in call_log.items():
            t = end
            for action_time, data in reversed(member_logs.items()):  # 최근 기록부터 과거로

                # 시간 내에 접속한 기록이 없으면 그 멤버는 표시하지 않음
                if member_id not in timeline:
                    if int(action_time) < start:
                        break
                    
                    timeline[member_id] = []
                
                # 그 시간의 상태 채우기
                match data["status"]:
                    case Status.JOIN.value:  # 들어간 시각부터 입장 상태로 표시
                        while t > int(action_time) and t > start:
                            timeline[member_id].append('🟩')
                            t -= INTERVAL
                    case Status.LEAVE.value:  # 나간 다음 시각부터 퇴장 상태로 표시
                        while t - INTERVAL > int(action_time) and t > start:
                            timeline[member_id].append('⬛')
                            t -= INTERVAL
                
                # 타임라인 왼쪽 끝에 도달하면 멈춤
                if t <= start:
                    break
            
            # 처음 액션까지 본 경우, 그 이전은 알 수 없기 때문에 빈칸으로 채움
            if member_id not in timeline:
                continue
            while t > start:
                timeline[member_id].append('▪️')
                t -= INTERVAL
        
        # 임베드 생성
        embed = discord.Embed(title="타임라인", color=0x78b159)
        if timeline:
            
            # 옆쪽에 닉네임 표시
            members = []
            for id in map(int, timeline):
                try:
                    member = guild.get_member(id) or await guild.fetch_member(id)
                    
                except discord.HTTPException:  # 서버에 멤버가 없으면
                    user = await self.bot.get_or_fetch_user(id)
                    members.append(f"{user.display_name}")
                    
                else:
                    if member.name != member.display_name:
                        members.append(f"{member.display_name} ({member.name})")
                    else:
                        members.append(f"{member.name}")
            
            embed.add_field(name="멤버", value='\n'.join(members))
            
            # 위쪽에 시간 표시
            hour = datetime.fromtimestamp(current, CallLog.TIMEZONE).hour
            clock, i = "", hour
            for _ in range(time_span):
                clock = CallLog.CLOCK_ICONS[i] + clock
                i = (i - 1) % 24
            
            embed.add_field(name=clock, value='\n'.join(''.join(reversed(value)) for value in timeline.values()))
            
        else:
            embed.description = "통화 기록이 없네요... :("
        
        embed.set_footer(text="NosookBot", icon_url=guild.icon.url if guild.icon else self.bot.user.display_avatar.url)
        embed.timestamp = datetime.now(CallLog.TIMEZONE)
        return embed
    
    
    @commands.slash_command(name="타임라인", description="통화 기록을 보여줍니다.")
    async def slash_show_timeline(self, ctx: discord.ApplicationContext, time_span: discord.Option(
        int, "최근 n시간의 기록 조회 (기간이 길 경우 임베드가 잘릴 수 있음)", min_value=1, max_value=24, default=12)):
        await ctx.respond(embed=await self.make_timeline_embed(ctx.guild, time_span))
    
    
    @commands.has_permissions(manage_channels=True)
    @commands.slash_command(name="리얼타임", description="해당 채널을 실시간 타임라인이 뜨는 채널로 설정합니다.")
    async def slash_set_realtime_channel(self, ctx: discord.ApplicationContext):
        channel_id = db.reference(f"realtime_channel/{ctx.guild.id}/channel").get()
        if channel_id == ctx.channel.id:
            await ctx.respond("이미 실시간 타임라인 채널로 설정되어 있습니다.", ephemeral=True)
            return
        
        class Button(discord.ui.View):
            @discord.ui.button(label="예", style=discord.ButtonStyle.green)
            async def button_yes(self_, button: discord.ui.Button, interaction: discord.Interaction):
                
                # 실시간 타임라인 채널로 설정
                timeline = await interaction.channel.send(embed=await self.make_timeline_embed(interaction.guild))
                db.reference(f"realtime_channel/{ctx.guild.id}").update({
                    "channel": ctx.channel.id,
                    "message": timeline.id
                })
                await confirm.edit_original_response(content="채널을 **실시간 타임라인 채널**로 설정했습니다!", view=None)
                
                permissions = timeline.channel.permissions_for(timeline.guild.me)
                if permissions.manage_channels:
                    await timeline.channel.edit(topic=f"타임라인 이외의 메시지는 {CallLog.MSG_DELETE_DELAY_MIN}분 뒤에 삭제됩니다.")
                if permissions.manage_messages:
                    await timeline.pin(reason="실시간 타임라인 메시지 고정")
                    await CallLog.clear_other_messages(timeline.channel, timeline.id)
            
            @discord.ui.button(label="아니요", style=discord.ButtonStyle.red)
            async def button_no(self, button: discord.ui.Button, interaction: discord.Interaction):
                await confirm.edit_original_response(content="실시간 타임라인 채널 등록을 취소하였습니다.", view=None)
        
        confirm = await ctx.respond(f"""
이 채널을 **실시간 타임라인 채널**로 설정할까요? 설정 시 **다른 모든 메시지는 삭제됩니다.**
이후 올라오는 메시지는 {CallLog.MSG_DELETE_DELAY_MIN}분 뒤에 삭제되므로, 타임라인에 대한 대화가 가능합니다.""",
                                    view=Button(), ephemeral=True)
    
    
    @staticmethod
    async def clear_other_messages(channel: discord.TextChannel, timeline_id: int):
        """ 실시간 타임라인 채널에서 타임라인 이외의 메시지를 모두 삭제한다. """
        
        if not channel.permissions_for(channel.guild.me).manage_messages:
            log(f"서버 {channel.guild.id}의 메시지 삭제 권한이 없습니다.")
            return
        
        async for message in channel.history(limit=None):
            if message.id != timeline_id:
                await message.delete()
    
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.channel or not message.guild:
            return
        
        # 실시간 타임라인 채널에 올라오는 메시지는 일정 시간 뒤에 삭제
        if message.channel.id == db.reference(f"realtime_channel/{message.guild.id}/channel").get():
            if message.channel.permissions_for(message.guild.me).manage_messages:
                await message.delete(delay=CallLog.MSG_DELETE_DELAY_MIN * 60, reason="실시간 타임라인 채널 메시지 삭제")
    
    
    @tasks.loop(minutes=1)
    async def task_update_timeline_every_hour(self):
        """ 매 시 정각마다 타임라인을 업데이트하는 루프 """
        now = datetime.now(CallLog.TIMEZONE)
        if now.minute != 0:
            return
        
        log(f"{now.hour}시 정각! 타임라인 업데이트 중...")
        for guild_id in db.reference("realtime_channel").get():
            try:
                guild = self.bot.get_guild(int(guild_id)) or await self.bot.fetch_guild(int(guild_id))
            except discord.errors.NotFound:
                log(f"서버 {guild_id}를 찾을 수 없습니다.")
            else:
                await self.update_realtime_timeline(guild)
        log("업데이트 완료")
    


@cog_logger
def setup(bot: discord.Bot):
    bot.add_cog(CallLog(bot))
