import discord
from os import environ
from os.path import exists
from base64 import b64decode
import firebase_admin
from firebase_admin import db as firebase_db
from nosookbot import NosookBot


class FirebaseDB(discord.Cog):
    """ 노숙봇 DB의 파이어베이스 구현체 """
    
    def __init__(self, bot: NosookBot):
        self.bot = bot
    
    
    def login(self):
        """ 파이어베이스 로그인 """
        
        if firebase_admin._apps:
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
        
        cred = firebase_admin.credentials.Certificate(fb_admin)
        database_url = environ["DATABASE_URL"]
        firebase_admin.initialize_app(cred, {"databaseURL": database_url})
        NosookBot.log("파이어베이스 로드 완료")
    
    def get(self, path: str) -> dict | str:
        """ 파이어베이스 데이터 읽기 """
        return firebase_db.reference(path).get() or {}
    
    def update(self, path: str, value: dict):
        """ 파이어베이스 데이터 업데이트 """
        firebase_db.reference(path).update(value)


@NosookBot.cog_logger
def setup(bot: NosookBot):
    bot.add_cog(FirebaseDB(bot))
