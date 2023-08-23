"""
* log(message): 로그를 콘솔에 출력한다.
"""

from datetime import datetime
from pytz import timezone


def log(message: str):
    """ 로그를 콘솔에 출력한다. """
    time = datetime.now(timezone('Asia/Seoul')).strftime("%y%m%d%H%M%S")
    print(f"[{time}] {message}")
