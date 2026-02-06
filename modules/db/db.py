import discord
from nosookbot import NosookBot
from .firebase import FirebaseDB


class DB(discord.Cog):
    """ 노숙봇 DB 인터페이스. 현재 파이어베이스 구현체 사용 중 """
    
    def __init__(self, bot: NosookBot):
        self.bot = bot
        
        bot.load_extension(FirebaseDB.__module__)
        self.firebase: FirebaseDB = bot.get_cog(FirebaseDB.__name__)
    
    
    def initialize(self):
        """ DB 로그인 """
        NosookBot.log("DB 초기화 중...")
        self.firebase.login()
        NosookBot.log("DB 초기화 완료")
    
    def read(self, path: str) -> dict | str:
        """ DB의 해당 경로에서 데이터 읽기 """
        return self.firebase.get(path)
    
    def update(self, path: str, value: dict):
        """ DB의 해당 경로에 데이터 업데이트 """
        self.firebase.update(path, value)


@NosookBot.cog_logger
def setup(bot: NosookBot):
    bot.add_cog(DB(bot))
