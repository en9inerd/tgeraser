"""
Tool deletes all your messages from chat/channel/dialog on Telegram.

Usage:
    tgeraser [ (session <session_name>) -cdl NUM [ -i FILEPATH | -j DICT | -e ] -p PEER_ID ] | [ -k ]
    tgeraser session <session_name> -p PEER_ID -t STRING
    tgeraser session <session_name> -w
    tgeraser -h | --help
    tgeraser --version

Options:
    -i --input-file FILEPATH    Specify YAML file that contains credentials. [default: ~/.tgeraser/credentials.yml]
    -j --json DICT              Specify json string that contains credentials (double quotes must be escaped).
    -e --environment-variables  Get credentials from environment variables (TG_API_ID, TG_API_HASH, TG_SESSION).
    -d --dialogs                List only Dialogs (Chats by default).
    -c --channels               List only Channels (Chats by default).
    -w --wipe-everything        Delete ALL messages from all chats/channels/dialogs that you have in list.
    -p --peers PEER_ID          Specify certain peers by comma (chat/channel/dialog).
    -l --limit NUM              Show specified number of recent chats.
    -t --time-period STRING     Specify period for infinite loop to run messages deletion every X seconds/minutes/hours/days/weeks.
                                Example: --time-period "3*days" OR --time-period "5*seconds"
    -k --kill                   Kill existing background tgeraser processes (only for Unix-like OS).
    -h --help                   Show this screen.
    --version                   Show version.

"""  # pylint: disable=line-too-long

import asyncio
import os
import signal
import subprocess
import sys
import time

from docopt import docopt

from .eraser import Eraser
from .__version__ import VERSION
from .exceptions import TgEraserException
from .utils import cast_to_int, get_credentials

loop = asyncio.get_event_loop()


def entry() -> None:
    """
    Entry function
    """
    arguments = docopt(__doc__, version=VERSION)
    if arguments["--limit"]:
        arguments["--limit"] = cast_to_int(arguments["--limit"], "limit")
    if arguments["--time-period"]:
        periods = {
            "seconds": 1,
            "minutes": 60,
            "hours": 3600,
            "days": 86400,
            "weeks": 604800,
        }
        period = arguments["--time-period"].split("*")
        if period[1] not in periods:
            raise TgEraserException("Time period is specified incorrectly.")

    if arguments["--kill"]:
        if os.name != "posix":
            raise TgEraserException("You can't use '--kill' option on Windows.")
        cmd = subprocess.Popen(["ps", "-A"], stdout=subprocess.PIPE)
        out = cmd.communicate()[0]
        current_pid = os.getpid()
        for line in out.splitlines():
            if b"tgeraser" in line:
                pid = int(line.split(None, 1)[0])
                if current_pid != pid:
                    os.kill(pid, signal.SIGKILL)
                    print("Process " + str(pid) + " successfully killed.")
        sys.exit(0)

    try:
        credentials = get_credentials(arguments)

        kwargs = {
            **credentials,
            "dialogs": arguments["--dialogs"],
            "channels": arguments["--channels"],
            "peers": arguments["--peers"],
            "limit": arguments["--limit"],
            "wipe_everything": arguments["--wipe-everything"]
        }

        client = Eraser(**kwargs)
        while True:
            loop.run_until_complete(client.run())
            if arguments["--time-period"]:
                print(
                    "\n({0})\tNext erasing will be in {1} {2}.".format(
                        time.strftime("%Y-%m-%d, %H:%M:%S", time.gmtime()),
                        period[0],
                        period[1],
                    )
                )
                time.sleep(int(period[0]) * periods[period[1]])
            else:
                break
        client.disconnect()
        loop.close()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as err:
        raise TgEraserException(err) from err


if __name__ == "__main__":
    entry()
