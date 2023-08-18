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

def get_cogs() -> list[str]:
    """ Cogs 폴더에 있는 모든 Cog 목록을 반환한다. Cogs.Core가 제일 먼저 있다. """
    cogs = list(map(lambda cog: f"Cogs.{cog[:-3]}",
        filter(lambda file: file.endswith(".py"), listdir("Cogs"))))
    cogs.sort(key=lambda cog: cog != "Cogs.Core")
    return cogs

def cog_logger(setup):
    """ Cog 로드 시 로그를 출력하는 데코레이터 """
    def wrapper(bot: discord.Bot):
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
