"""
Tool deletes all your messages from chat/channel/conversation on Telegram.

Usage:
    tgeraser [(session <session_name>) --entity-type TYPE -l NUM [-d PATH] -p PEER_ID -o STRING] | [-k]
    tgeraser session <session_name> -p PEER_ID -t STRING [-o STRING]
    tgeraser session <session_name> -w [--entity-type TYPE -o STRING]
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
    -o --older-than STRING      Delete messages older than X seconds/minutes/hours/days/weeks.
                                Example: --older-than "3*days" OR --older-than "5*seconds"
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
from .utils import cast_to_int, get_credentials, parse_time_period


def signal_handler(sig=signal.SIGINT, frame=None):
    """
    Signal handler
    """
    print("\nCtrl+C captured, exiting...")
    sys.stdout.flush()
    os._exit(0)


async def main() -> None:
    """
    Entry function
    """
    if os.name == "posix":
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, signal_handler)
    else:
        signal.signal(signal.SIGINT, signal_handler)

    arguments = docopt(__doc__, version=VERSION)
    limit = cast_to_int(arguments["--limit"], "limit") if arguments["--limit"] else None
    period = (
        parse_time_period(arguments["--time-period"], "--time-period")
        if arguments["--time-period"]
        else None
    )
    older_than = (
        parse_time_period(arguments["--older-than"], "--older-than")["time"]
        if arguments["--older-than"]
        else None
    )

    if arguments["--kill"]:
        kill_existing_processes()
        sys.exit(0)

    try:
        credentials = await get_credentials(arguments)
        kwargs = {
            **credentials,
            "peers": arguments["--peers"],
            "limit": limit,
            "wipe_everything": arguments["--wipe-everything"],
            "entity_type": arguments["--entity-type"],
            "older_than": older_than,
        }
        await run_eraser(kwargs, period if arguments["--time-period"] else None)
    except ValueError as err:
        print(f"ValueError: {err}")
    except TgEraserException as err:
        print(f"TgEraserException: {err}")
    except Exception as err:
        raise TgEraserException(f"An unexpected error occurred: {err}") from err


async def run_eraser(kwargs: dict, period: dict = None) -> None:
    """
    Runs the eraser
    """
    client = Eraser(**kwargs)
    try:
        while True:
            await client.init()
            await client.run()
            if period:
                print(
                    "\n({0})\tNext erasing will be in {1} {2}.".format(
                        time.strftime("%Y-%m-%d, %H:%M:%S", time.gmtime()),
                        period["value"],
                        period["unit"],
                    )
                )
                await asyncio.sleep(period["time"])
            else:
                break
    finally:
        await client.disconnect()


def kill_existing_processes():
    """
    Kills existing background TgEraser processes
    """
    if os.name != "posix":
        raise TgEraserException("You can't use '--kill' option on Windows.")
    cmd = subprocess.Popen(["ps", "-A"], stdout=subprocess.PIPE)
    out, _ = cmd.communicate()
    current_pid = os.getpid()
    for line in out.splitlines():
        if b"tgeraser" in line:
            pid = int(line.split(None, 1)[0])
            if current_pid != pid:
                os.kill(pid, signal.SIGKILL)
                print("Process " + str(pid) + " successfully killed.")


def entry() -> None:
    """
    Entry point function
    """
    asyncio.run(main())


if __name__ == "__main__":
    entry()
