import discord
from discord.ext import commands
from os import getenv
from os.path import exists
from base64 import b64decode
import firebase_admin as firebase
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
    


@cog_logger
def setup(bot: discord.Bot):
    bot.add_cog(CallLog(bot))
