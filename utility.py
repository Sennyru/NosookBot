"""
* log(message): 로그를 콘솔에 출력한다.
* get_cogs() -> map: Cogs 폴더에 있는 모든 Cog 목록을 반환한다.
"""

from datetime import datetime
from pytz import timezone
from os import listdir


def log(message: str):
    """ 로그를 콘솔에 출력한다. """
    time = datetime.now(timezone('Asia/Seoul')).strftime("%y/%m/%d %H:%M:%S")
    print(f"[{time}] {message}")

def get_cogs() -> map:
    """ Cogs 폴더에 있는 모든 Cog 목록을 반환한다. """
    return map(lambda cog: f"Cogs.{cog[:-3]}",
        filter(lambda file: file.endswith(".py"), listdir("Cogs")))
