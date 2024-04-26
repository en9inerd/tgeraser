"""
Tool deletes all your messages from chat/channel/conversation on Telegram.

Usage:
    tgeraser [(session <session_name>) --entity-type TYPE -l NUM [-d PATH] -p PEER_ID] | [-k]
    tgeraser session <session_name> -p PEER_ID -t STRING
    tgeraser session <session_name> -w [--entity-type TYPE]
    tgeraser -h | --help
    tgeraser --version

Options:
    -d --directory PATH         Specify a directory where your sessions are stored. [default: ~/.tgeraser/]
    -w --wipe-everything        Delete all messages from all entities of a certain type that you have in your dialog list.
    --entity-type TYPE          Available types: any, chat, channel, user. [default: chat]
    -p --peers PEER_ID          Specify certain peers by comma (chat/channel/user).
    -l --limit NUM              Show a specified number of recent chats.
    -t --time-period STRING     Specify a period for an infinite loop to run messages deletion every X seconds/minutes/hours/days/weeks.
                                Example: --time-period "3*days" OR --time-period "5*seconds"
    -k --kill                   Terminate existing background TgEraser processes (only for Unix-like OS).
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

from .__version__ import VERSION
from .eraser import Eraser
from .exceptions import TgEraserException
from .utils import cast_to_int, get_credentials


def signal_handler():
    print("\nCtrl+C captured, exiting...")
    sys.stdout.flush()
    os._exit(0)


async def main() -> None:
    """
    Entry function
    """
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, signal_handler)

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
        credentials = await get_credentials(arguments)

        kwargs = {
            **credentials,
            "peers": arguments["--peers"],
            "limit": arguments["--limit"],
            "wipe_everything": arguments["--wipe-everything"],
            "entity_type": arguments["--entity-type"],
        }

        client = Eraser(**credentials)
        while True:
            await client.init(**kwargs)
            await client.run()
            if arguments["--time-period"]:
                print(
                    "\n({0})\tNext erasing will be in {1} {2}.".format(
                        time.strftime("%Y-%m-%d, %H:%M:%S", time.gmtime()),
                        period[0],
                        period[1],
                    )
                )
                await asyncio.sleep(int(period[0]) * periods[period[1]])
            else:
                break
        await client.disconnect()
    except Exception as err:
        raise TgEraserException(err) from err


def entry() -> None:
    """
    Entry point function
    """
    asyncio.run(main())


if __name__ == "__main__":
    entry()
