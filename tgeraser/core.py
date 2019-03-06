# coding=utf-8
"""
Tool erases all your messages from chat/channel/dialog on Telegram.

Usage:
    tgeraser [ (session <session_name>) -di=FILENAME -p=ID -lt=NUM ]
    tgeraser (-h | --help)
    tgeraser --version

Options:
    -i --input-file=FILENAME    Specify input YAML file. [default: ~/.tgeraser/credentials.yml]
    -d --dialogs                List only Dialogs (Channels & Chats by default).
    -p --peer=ID                Specify certain peer (chat/channel/dialog).
    -l --limit=NUM              Show specified number of recent chats.
    -t --time-period=NUM        Specify period for infinite loop to run message erasing every NUM seconds. [default: 0]
    -h --help                   Show this screen.
    --version                   Show version.

"""

import sys
import traceback

from docopt import docopt

from . import Eraser
from .__version__ import __version__
from .utils import check_num, get_credentials


def entry() -> None:
    """
    Entry function
    """
    arguments = docopt(__doc__, version=__version__)
    check_num("limit", arguments["--limit"])
    check_num("time", arguments["--time"])

    try:
        credentials = get_credentials(
            path=arguments["--input-file"],
            session_name=arguments["<session_name>"] if arguments["session"] else None,
        )

        kwargs = {
            **credentials,
            "dialogs": arguments["--dialogs"],
            "peer": arguments["--peer"],
            "limit": arguments["--limit"],
        }

        client = Eraser(**kwargs)
        client.run()
        print("\nErasing is finished.\n")
        client.disconnect()
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception:
        traceback.print_exc(file=sys.stdout)
    exit(0)


if __name__ == "__main__":
    entry()
