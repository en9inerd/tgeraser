# coding=utf-8
"""
Tool erases all your messages from chat/channel/dialog on Telegram.

Usage:
    tgeraser [ (session <session_name>) -di=FILENAME -p=ID -t=NUM ]
    tgeraser (-h | --help)
    tgeraser --version

Options:
    -i --input-file=FILENAME    Specify input YAML file. [default: ~/.tgeraser/credentials.yml]
    -d --dialogs                List only Dialogs (Channels & Chats by default).
    -p --peer=ID                Specify certain peer (chat/channel/dialof).
    -t --time-period=NUM        Specify period for infinite loop to run message erasing every NUM seconds. [default: 0]
    -h --help                   Show this screen.
    --version                   Show version.

"""

import sys, traceback
from docopt import docopt

from . import Eraser
from .__version__ import __version__
from .utils import get_credentials


def entry() -> None:
    """
    Entry function
    """
    arguments = docopt(__doc__, version=__version__)

    try:
        credentials = get_credentials(
            path=arguments["--input-file"],
            session_name=arguments["<session_name>"] if arguments["session"] else None,
        )

        client = Eraser(**credentials, dialogs=arguments["--dialogs"])
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
