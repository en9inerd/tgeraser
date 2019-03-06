# coding=utf-8
"""
Tool erases all your messages from chat/channel/dialog on Telegram.

Usage:
    tgeraser [ (session <session_name>) -dl=NUM [ -i=FILENAME | -j=DICT ] -p=ID -t=NUM ] | [ -k ]
    tgeraser (-h | --help)
    tgeraser --version

Options:
    -i --input-file=FILENAME    Specify YAML file that contains credentials. [default: ~/.tgeraser/credentials.yml]
    -j --json=DICT              Specify json string that contains credentials (double quotes must be escaped).
    -d --dialogs                List only Dialogs (Channels & Chats by default).
    -p --peer=ID                Specify certain peer (chat/channel/dialog).
    -l --limit=NUM              Show specified number of recent chats.
    -t --time-period=NUM        Specify period for infinite loop to run message erasing every NUM seconds.
    -k --kill                   Kill background process if you specify --time option (only for Unix-like OS).
    -h --help                   Show this screen.
    --version                   Show version.

"""

import os
import signal
import subprocess
import sys
import time
import traceback

from docopt import docopt

from . import Eraser
from .__version__ import __version__
from .exceptions import TgEraserException
from .utils import check_num, get_credentials_from_yaml, get_credentials_from_json


def entry() -> None:
    """
    Entry function
    """
    arguments = docopt(__doc__, version=__version__)
    if arguments["--limit"]:
        check_num("limit", arguments["--limit"])
    if arguments["--time-period"]:
        check_num("time", arguments["--time-period"])

    if arguments["--kill"]:
        if os.name != "posix":
            raise TgEraserException("You can't use '--kill' option on Windows.")
        cmd = subprocess.Popen(["ps", "-A"], stdout=subprocess.PIPE)
        out = cmd.communicate()[0]
        for line in out.splitlines():
            if "tgeraser" in line:
                pid = int(line.split(None, 1)[0])
                os.kill(pid, signal.SIGKILL)

    try:
        if arguments["--json"]:
            credentials = get_credentials_from_json(arguments["--json"])
        else:
            credentials = get_credentials_from_yaml(
                path=arguments["--input-file"],
                session_name=arguments["<session_name>"]
                if arguments["session"]
                else None,
            )

        kwargs = {
            **credentials,
            "dialogs": arguments["--dialogs"],
            "peer": arguments["--peer"],
            "limit": arguments["--limit"],
        }

        while True:
            client = Eraser(**kwargs)
            client.run()
            client.disconnect()
            if arguments["--time-period"]:
                print(
                    "({0})\tNext erasing will be in {1} seconds.".format(
                        time.strftime("%Y-%m-%d, %H:%M:%S", time.gmtime()),
                        arguments["--time-period"],
                    )
                )
                time.sleep(int(arguments["--time-period"]))
            else:
                break
        print("\nErasing is finished.\n")
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception:
        traceback.print_exc(file=sys.stdout)


if __name__ == "__main__":
    entry()
