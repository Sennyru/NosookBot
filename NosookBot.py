import discord
from os import listdir
from pytz import timezone
from utility import log


class NosookBot(discord.Bot):
    """ discord.Bot 확장 클래스 """
    
    color = 0x8fd26a
    timezone = timezone('Asia/Seoul')
    
    def __init__(self, dev: bool, description=None, *args, **options):
        super().__init__(description, *args, **options)
        self.dev = dev
    
    @staticmethod
    def get_cogs() -> list[str]:
        """ Cogs 폴더에 있는 모든 Cog 목록을 반환한다. Cogs.Core가 제일 먼저 있다. """
        
        cogs = list(map(lambda cog: f"Cogs.{cog[:-3]}",
                        filter(lambda file: file.endswith(".py"), listdir("Cogs"))))
        cogs.sort(key=lambda cog: cog != "Cogs.Core")
        return cogs
    
    @staticmethod
    def cog_logger(setup):
        """ Cog 로드 시 로그를 출력하는 데코레이터 """
        
        def wrapper(bot: NosookBot):
            cog_name = setup.__module__
            log(f"{cog_name} 로드 중...")
            try:
                setup(bot)
            except Exception as error:
                log(f"{cog_name} 로드 실패! 아래 예외를 확인하세요.")
                log(error)
            else:
                log(f"{cog_name} 로드 완료")
        
        return wrapper
    
