import discord
from os import listdir
from pytz import timezone
from datetime import datetime


class NosookBot(discord.Bot):
    """ discord.Bot 확장 클래스 """
    
    github = "https://github.com/Secon0101/NosookBot"
    color = 0x8fd26a
    timezone = timezone("Asia/Seoul")
    cogs = []
    owner_mention = None
    
    
    def __init__(self, dev: bool, description=None, *args, **options):
        super().__init__(description, *args, **options)
        self.dev = dev
        self.owner_mention = f"<@{self.owner_ids[0]}>"
        
        # Cogs/*.py cog 목록 가져오기
        self.cogs = list(map(lambda cog: f"Cogs.{cog[:-3]}",
                         filter(lambda file: file.endswith(".py"), listdir("Cogs"))))
        self.cogs.sort(key=lambda cog: cog != "Cogs.core")
        self.load_extensions(*self.cogs)
    
    @staticmethod
    def log(message):
        """ 로그를 콘솔에 출력한다. """
        
        time = datetime.now(NosookBot.timezone).strftime("%y%m%d%H%M%S")
        print(f"[{time}] {message}")
    
    @staticmethod
    def cog_logger(setup):
        """ Cog 로드 시 로그를 출력하는 데코레이터 """
        
        def wrapper(bot: NosookBot):
            cog_name = setup.__module__
            NosookBot.log(f"{cog_name} 로드 중...")
            try:
                setup(bot)
            except Exception as error:
                NosookBot.log(f"{cog_name} 로드 실패! 아래 예외를 확인하세요.")
                NosookBot.log(error)
            else:
                NosookBot.log(f"{cog_name} 로드 완료")
        
        return wrapper
    
