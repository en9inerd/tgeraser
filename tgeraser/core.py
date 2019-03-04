# coding=utf-8
"""Script deletes all your messages from chat/dialog in Telegram. This version is more faster than script from original repo.

Usage:
    tgeraser [(session <session_name>) [-c | -d]]
    tgeraser (-h | --help)
    tgeraser --version

Options:
    -c --channels   List only Channels - default.
    -d --dialogs    List only Dialogs.
    -h --help       Show this screen.
    --version       Show version.

"""

from docopt import docopt

from . import Eraser
from .__version__ import __version__
from .utils import get_credentials


def entry() -> None:
    """
    Entry function
    """
    arguments = docopt(__doc__, version=__version__)

    credentials = get_credentials(
        path=None,
        session_name=arguments["<session_name>"] if arguments["session"] else None,
    )

    client = Eraser(**credentials, dialogs=arguments["--dialogs"])
    client.run()
    print("\nDeletion is finished.\n")
    client.disconnect()


if __name__ == "__main__":
    entry()
