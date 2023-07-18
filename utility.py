"""
* log(message): 로그를 콘솔에 출력한다.
* get_cogs() -> map: Cogs 폴더에 있는 모든 Cog 목록을 반환한다.
* @cog_logger: Cog 로드 시 로그를 출력하는 데코레이터
"""

import discord
from datetime import datetime
from os import listdir
from pytz import timezone


def log(message: str):
    """ 로그를 콘솔에 출력한다. """
    time = datetime.now(timezone('Asia/Seoul')).strftime("%y%m%d%H%M%S")
    print(f"[{time}] {message}")

def get_cogs() -> map:
    """ Cogs 폴더에 있는 모든 Cog 목록을 반환한다. """
    return map(lambda cog: f"Cogs.{cog[:-3]}",
        filter(lambda file: file.endswith(".py"), listdir("Cogs")))

def cog_logger(setup):
    """ Cog 로드 시 로그를 출력하는 데코레이터 """
    def wrapper(bot: discord.Bot):
        log(f"{setup.__module__} 로드 중...")
        setup(bot)
        log(f"{setup.__module__} 로드 완료")
    return wrapper
