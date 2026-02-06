import discord
from pytz import timezone
from datetime import datetime
from traceback import format_exc


class NosookBot(discord.Bot):
    """ discord.Bot 확장 클래스 """
    
    github = "https://github.com/Sennyru/NosookBot"
    color = 0x8fd26a
    timezone = timezone("Asia/Seoul")
    owner_mention = None
    
    
    def __init__(self, is_alpha_channel: bool, cog_names: list, description=None, *args, **options):
        super().__init__(description, *args, **options)
        self.release_channel = "alpha" if is_alpha_channel else "release"
        self.owner_mention = f"<@{self.owner_ids[0]}>"
        
        # load cogs
        self.cog_names = cog_names
        self.load_extensions(*self.cog_names)
    
    
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
            except:
                NosookBot.log(f"{cog_name} 로드 실패! 아래 예외를 확인하세요.")
                print(format_exc())
            else:
                NosookBot.log(f"{cog_name} 로드 완료")
        
        return wrapper
