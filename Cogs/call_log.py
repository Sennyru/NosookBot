import discord
from discord.ext import commands, tasks
from enum import Enum
from os import environ
from os.path import exists
from base64 import b64decode
import firebase_admin as firebase
from firebase_admin import db
from datetime import datetime
from time import time
from traceback import format_exc
from nosookbot import NosookBot


class Status(Enum):
    JOIN = 1
    LEAVE = 0
    AFK = 2


class CallLog(commands.Cog):
    
    CLOCK_ICONS = "🕧🕜🕝🕞🕟🕠🕡🕢🕣🕤🕥🕦🕧🕜🕝🕞🕟🕠🕡🕢🕣🕤🕥🕦"
    MSG_DELETE_DELAY_MIN = 60
    
    
    def __init__(self, bot: NosookBot):
        self.bot = bot
        
        # 파이어베이스
        if firebase._apps:
            NosookBot.log("이미 파이어베이스에 연결됨")
            return
        
        NosookBot.log("파이어베이스 연결 중...")
        fb_admin = "firebase-admin.json"
        
        # 파일이 없거나 비어 있으면 생성
        need_to_create = False
        if not exists(fb_admin):
            need_to_create = True
            NosookBot.log(f"{fb_admin} 파일 없음. 생성 중...")
        else:
            with open(fb_admin, 'r') as f:
                if not f.read():
                    need_to_create = True
                    NosookBot.log(f"{fb_admin} 파일 비어있음. 생성 중...")
        if need_to_create:
            with open(fb_admin, 'w') as f:
                fb_admin_base64 = environ["FIREBASE_ADMIN_BASE64"]
                f.write(b64decode(fb_admin_base64).decode("utf-8"))
            NosookBot.log(f"{fb_admin} 생성 완료")
        
        cred = firebase.credentials.Certificate(fb_admin)
        database_url = environ["DATABASE_URL"]
        firebase.initialize_app(cred, {"databaseURL": database_url})
        NosookBot.log("파이어베이스 로드 완료")
    
    
    @commands.Cog.listener()
    async def on_ready(self):
        if not self.task_update_timeline_every_hour.is_running():
            self.task_update_timeline_every_hour.start()
        
        # 실시간 타임라인 업데이트
        NosookBot.log("실시간 타임라인 채널 초기화 중...")
        realtime_data: dict = db.reference(f"{self.bot.release_channel}/realtime_channel").get() or {}
        
        for guild_id in realtime_data:
            # 길드 찾기
            guild = self.bot.get_guild(int(guild_id))
            if guild is None:
                try:
                    guild = await self.bot.fetch_guild(guild_id)
                except discord.errors.NotFound:
                    NosookBot.log(f"서버 {guild_id}를 찾을 수 없습니다.")
                    continue
            
            # 리얼타임 채널 찾기
            channel_id = int(realtime_data[guild_id]["channel"])
            channel = guild.get_channel(channel_id)
            if channel is None:
                try:
                    channel = await guild.fetch_channel(channel_id)
                except discord.errors.NotFound:
                    NosookBot.log(f"서버 {guild_id}의 타임라인 채널({channel_id})을 찾을 수 없습니다.")
                    continue
                except discord.errors.Forbidden:
                    NosookBot.log(f"서버 {guild_id}의 타임라인 채널({channel_id})에 접근할 수 없습니다.")
                    continue
            
            # 타임라인 업데이트
            await self.update_realtime_timeline(guild)
            
            # 채팅 클리어
            await CallLog.clear_other_messages(channel, int(realtime_data[guild_id]["message"]))
        
        NosookBot.log("초기화 완료")
    
    
    async def update_realtime_timeline(self, guild: discord.Guild):
        """ 서버의 실시간 타임라인 임베드를 새로 생성하고 업데이트한다. """
        
        if guild is None:
            return
        
        ref = db.reference(f"{self.bot.release_channel}/realtime_channel/{guild.id}")
        realtime_data: dict = ref.get()
        if realtime_data is None:
            return
        
        channel_id = int(realtime_data["channel"])
        realtime_channel = self.bot.get_channel(channel_id)
        if realtime_channel is None:
            try:
                realtime_channel = await self.bot.fetch_channel(channel_id)
            except discord.errors.NotFound:
                NosookBot.log(f"서버 {guild.id}의 타임라인 채널({channel_id})을 찾을 수 없습니다.")
                return
            except discord.errors.Forbidden:
                NosookBot.log(f"서버 {guild.id}의 타임라인 채널({channel_id})에 접근할 수 없습니다.")
                return
        
        message_id = int(realtime_data["message"])
        message = self.bot.get_message(message_id)
        if message is None:
            try:
                message = await realtime_channel.fetch_message(message_id)
            except discord.errors.NotFound:
                NosookBot.log(f"서버 {guild.id}의 타임라인 메시지({message_id})를 찾을 수 없습니다.")
                return
            except discord.errors.Forbidden:
                NosookBot.log(f"서버 {guild.id}의 타임라인 메시지({message_id})에 접근할 수 없습니다.")
                return
        
        if message.author == self.bot.user:
            await message.add_reaction("🔄")
            await message.edit(embed=await self.create_timeline_embed(guild))
            NosookBot.log(f"서버 {guild.id} 타임라인 업데이트됨")
            await message.remove_reaction("🔄", self.bot.user)
        else:
            NosookBot.log(f"서버 {guild.id}의 타임라인 메시지({message_id})를 수정할 수 없습니다. 혹시 노숙봇이 아니신가요?")
    
    
    async def create_timeline_embed(self, guild: discord.Guild, time_span=12, current=None) -> discord.Embed:
        """ 실시간 타임라인 임베드를 생성한다. """
        
        INTERVAL = 60 * 60  # 1시간
        
        if current is None:
            current = int(time())
        end = current - current % INTERVAL + INTERVAL  # 타임라인 오른쪽 끝 시각
        start = end - time_span * INTERVAL  # 타임라인 왼쪽 끝 시각
        call_log: dict[str, dict] = db.reference(f"{self.bot.release_channel}/call_log/{guild.id}").get() or {}
        timeline: dict[str, list] = {}  # 멤버별 타임라인 저장
        has_unknown = False  # 알 수 없음 상태가 있는지 여부
        
        # 뒤에 나올, 채우는 조건에 대한 식
        with_current = lambda: t > int(action_time)  # 현재 칸 포함
        without_current = lambda: t - INTERVAL > int(action_time)  # 현재 칸 제외
        
        # 타임라인 생성
        for member_id, member_logs in call_log.items():
            t = end
            for action_time, data in reversed(member_logs.items()):  # 최근 기록부터 과거로
                
                if member_id not in timeline:
                    # 시간 내에 접속한 기록이 없으면 그 멤버는 표시하지 않음
                    if int(action_time) < start and data["status"] == Status.LEAVE.value:
                        break
                    
                    timeline[member_id] = []
                
                # 상태 및 채우는 조건 설정
                icon, check = '▪️', without_current  # (기본값인데 무조건 수정됨)
                match data["status"]:  # (파이썬 3.10 이하는 수정 필요!!)
                    case Status.JOIN.value:
                        icon, check = '🟩', with_current
                    case Status.LEAVE.value:
                        icon, check = '⬛', without_current
                    case Status.AFK.value:
                        icon, check = '🟧', without_current
                
                # 현재 기록과 이후 기록 사이를 한 칸씩 채우기
                while check() and t > start:
                    timeline[member_id].append(icon)
                    t -= INTERVAL
                
                # 타임라인 왼쪽 끝에 도달하면 멈춤
                if t <= start:
                    break
            
            if member_id not in timeline:
                continue
            
            # 처음 액션까지 본 경우, 그 이전은 알 수 없기 때문에 빈칸으로 채움
            if t > start:
                has_unknown = True
                while t > start:
                    timeline[member_id].append('▪️')
                    t -= INTERVAL
        
        # 임베드 생성
        embed = discord.Embed(title="타임라인", color=0x78b159)
        icon_url = guild.icon.url if guild.icon else self.bot.user.display_avatar.url
        timestamp = datetime.fromtimestamp(current, NosookBot.timezone)
        
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
                        members.append(member.name)
            
            embed.add_field(name="멤버", value='\n'.join(members))
            
            # 위쪽에 시간 표시
            hour = timestamp.hour
            clock, i = "", hour
            for _ in range(time_span):
                clock = CallLog.CLOCK_ICONS[i] + clock
                i = (i - 1) % 24
            embed.add_field(name=clock, value='\n'.join(''.join(reversed(value)) for value in timeline.values()))
            
            footer_text = "🟩 통화 중  ⬛ 나감  ▪️ 알 수 없음" if has_unknown else "🟩 통화 중  ⬛ 나감"
            embed.set_footer(text=footer_text, icon_url=icon_url)
            
        else:
            embed.description = "통화 기록이 없네요... :("
            embed.set_footer(text="NosookBot", icon_url=icon_url)
        
        embed.timestamp = timestamp
        return embed
    
    
    @staticmethod
    async def clear_other_messages(channel: discord.TextChannel, timeline_id: int):
        """ 실시간 타임라인 채널에서 타임라인 이외의 메시지를 모두 삭제한다. """
        
        if not channel.permissions_for(channel.guild.me).manage_messages:
            NosookBot.log(f"서버 {channel.guild.id}의 메시지 삭제 권한이 없습니다.")
            return
        
        async for message in channel.history(limit=None):
            if message.id != timeline_id:
                await message.delete()
    
    
    @commands.slash_command(name="타임라인", description="통화 기록을 보여줍니다.")
    async def slash_show_timeline(self, ctx: discord.ApplicationContext, time_span: discord.Option(
        int, "최근 n시간의 기록 조회 (기간이 길 경우 임베드가 잘릴 수 있음)", min_value=1, max_value=24, default=12)):
        await ctx.defer()
        await ctx.respond(embed=await self.create_timeline_embed(ctx.guild, time_span))
    
    
    @commands.has_permissions(manage_channels=True)
    @commands.slash_command(name="리얼타임", description="해당 채널을 실시간 타임라인이 뜨는 채널로 설정합니다.")
    async def slash_set_realtime_channel(self, ctx: discord.ApplicationContext):
        channel_id = db.reference(f"{self.bot.release_channel}/realtime_channel/{ctx.guild.id}/channel").get()
        if channel_id == str(ctx.channel.id):
            await ctx.respond("이미 실시간 타임라인 채널로 설정되어 있습니다.", ephemeral=True)
            return
        
        class Button(discord.ui.View):
            @discord.ui.button(label="예", style=discord.ButtonStyle.green)
            async def button_yes(_, button: discord.ui.Button, interaction: discord.Interaction):
                
                # 실시간 타임라인 채널로 설정
                timeline = await interaction.channel.send(embed=await self.create_timeline_embed(interaction.guild))
                db.reference(f"{self.bot.release_channel}/realtime_channel/{ctx.guild.id}").update({
                    "channel": str(ctx.channel.id),
                    "message": str(timeline.id)
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
    
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member,
                                    before: discord.VoiceState, after: discord.VoiceState):
        # 채널이 바뀐 경우만 처리
        # 이론상 서버가 다르지는 않음
        if before.channel == after.channel:
            return
        
        # 이론상 불가능
        if before.channel is None and after.channel is None:
            return
        
        # on join
        elif before.channel is None and after.channel is not None:
            await self.update_call_log(member.id, Status.JOIN, after.channel)
            await self.update_realtime_timeline(after.channel.guild)
        
        # on leave
        elif before.channel is not None and after.channel is None:
            await self.update_call_log(member.id, Status.LEAVE, before.channel)
            await self.update_realtime_timeline(before.channel.guild)
        
        # on move channel
        else:
            print("move")
            if after.afk:  # afk로 이동
                await self.update_call_log(member.id, Status.AFK, after.channel)
                await self.update_realtime_timeline(after.channel.guild)
                print("after afk")
            elif before.afk:  # afk 해제
                await self.update_call_log(member.id, Status.JOIN, after.channel)
                await self.update_realtime_timeline(after.channel.guild)
                print("before afk")
    
    
    async def update_call_log(self, user_id: int, status: Status, channel: discord.VoiceChannel, action_time=None):
        """ 통화 기록을 데이터베이스에 저장한다. """
        
        if action_time is None:
            action_time = int(time())
        
        db.reference(f"{self.bot.release_channel}/call_log/{channel.guild.id}/{user_id}/{action_time}").update({
            "status": status.value,
            "channel": str(channel.id),
        })
    
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.channel or not message.guild:
            return
        
        # 실시간 타임라인 채널에 올라오는 메시지는 일정 시간 뒤에 삭제
        channel_data = db.reference(f"{self.bot.release_channel}/realtime_channel/{message.guild.id}").get() or {}
        if channel_data is None:
            return
        if not message.channel.id == int(channel_data["channel"]):
            return
        if not message.channel.permissions_for(message.guild.me).manage_messages:
            return
        if message.id == int(channel_data["message"]):
            return
        
        await message.delete(delay=CallLog.MSG_DELETE_DELAY_MIN * 60, reason="실시간 타임라인 채널 메시지 삭제")
    
    
    @tasks.loop(minutes=1)
    async def task_update_timeline_every_hour(self):
        """ 매 시 정각마다 타임라인을 업데이트하는 루프 """
        
        # task는 예외 발생 시 멈춰버려서 핸들링 필요
        try:
            now = datetime.now(NosookBot.timezone)
            if now.minute != 0:
                return

            NosookBot.log(f"{now.hour}시 정각! 타임라인 업데이트 중...")
            for guild_id in db.reference(f"{self.bot.release_channel}/realtime_channel").get():
                try:
                    guild = self.bot.get_guild(int(guild_id)) or await self.bot.fetch_guild(int(guild_id))
                except discord.errors.NotFound:
                    NosookBot.log(f"서버 {guild_id}를 찾을 수 없습니다.")
                else:
                    await self.update_realtime_timeline(guild)
            NosookBot.log("업데이트 완료")
            
        except:
            print(format_exc())
    


@NosookBot.cog_logger
def setup(bot: NosookBot):
    bot.add_cog(CallLog(bot))
