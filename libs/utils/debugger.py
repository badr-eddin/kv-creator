import os
import datetime
import traceback
from colorama import *

LOGS = [(), ]


def debug(*args, _c="i"):
    if os.getenv("dev-env"):
        if LOGS[-1] != args:
            LOGS.append(args)
            print(
                f"[{Fore.GREEN}{datetime.datetime.now().strftime('%H:%M:%S')}{Fore.RESET}]",
                {"i": Fore.BLUE, "e": Fore.RED, "w": Fore.YELLOW}.get(_c), *args, Fore.RESET)
