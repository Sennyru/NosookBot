import discord
from os import environ
from os.path import exists
from base64 import b64decode
import firebase_admin as firebase
from firebase_admin import db
from nosookbot import NosookBot


class Repository(discord.Cog):
    @staticmethod
    def initialize():
        """ 파이어베이스 로그인 """
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

    @staticmethod
    def read(path: str) -> dict | str:
        return db.reference(path).get() or {}

    @staticmethod
    def update(path: str, value: dict):
        db.reference(path).update(value)


@NosookBot.cog_logger
def setup(bot: NosookBot):
    bot.add_cog(Repository(bot))
