# TgEraser

Tool that deletes messages from chats, channels and dialogs

[![PyPI version](https://badge.fury.io/py/tgeraser.svg)](https://badge.fury.io/py/tgeraser)

## Installation

`pip install tgeraser`

## Usage

```
Tool deletes all your messages from chat/channel/dialog on Telegram.

Usage:
    tgeraser [ (session <session_name>) -dl=NUM [ -i=FILENAME | -j=DICT ] -p=ID -t=NUM ] | [ -k ]
    tgeraser (-h | --help)
    tgeraser --version

Options:
    -i --input-file=FILENAME    Specify YAML file that contains credentials. [default: ~/.tgeraser/credentials.yml]
    -j --json=DICT              Specify json string that contains credentials (double quotes must be escaped).
    -e --environment-variables  Get credentials from environment variables ().
    -d --dialogs                List only Dialogs (Channels & Chats by default).
    -p --peer=ID                Specify certain peer (chat/channel/dialog).
    -l --limit=NUM              Show specified number of recent chats.
    -t --time-period=NUM        Specify period for infinite loop to run message erasing every NUM seconds.
    -k --kill                   Kill background process if you specify --time option (only for Unix-like OS).
    -h --help                   Show this screen.
    --version                   Show version.
```
