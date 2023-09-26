# TgEraser

[![PyPI version](https://badge.fury.io/py/tgeraser.svg)](https://badge.fury.io/py/tgeraser)

Tool deletes all of your messages from chat/channel/dialog on Telegram without admin privilege. Official Telegram clients don't support deletion for all own messages from chat with one click (you need to manually select messages that you want to delete and you can delete only 100 selected meesages per time).

TgEraser decides this problem.

## Installation

```
pip install tgeraser
tgeraser
```

You need to specify own api_id and api_hash which you can get [here](https://my.telegram.org/auth?to=apps)

## Usage

```
Tool deletes all your messages from chat/channel/dialog on Telegram.

Usage:
    tgeraser [(session <session_name>) --entity-type TYPE -l NUM [-i FILEPATH | -j DICT | -e] -p PEER_ID] | [-k]
    tgeraser session <session_name> -p PEER_ID -t STRING
    tgeraser session <session_name> -w [--entity-type TYPE]
    tgeraser -h | --help
    tgeraser --version

Options:
    -i --input-file FILEPATH    Specify YAML file that contains credentials. [default: ~/.tgeraser/credentials.yml]
    -j --json DICT              Specify json string that contains credentials (double quotes must be escaped).
    -e --environment-variables  Get credentials from environment variables (TG_API_ID, TG_API_HASH, TG_SESSION).
    -w --wipe-everything        Delete ALL messages from all entities of a certain type that you have in list.
    --entity-type TYPE          Available types: any, chat, channel, dialog. [default: chat]
    -p --peers PEER_ID          Specify certain peers by comma (chat/channel/dialog).
    -l --limit NUM              Show specified number of recent chats.
    -t --time-period STRING     Specify period for infinite loop to run messages deletion every X seconds/minutes/hours/days/weeks.
                                Example: --time-period "3*days" OR --time-period "5*seconds"
    -k --kill                   Kill existing background tgeraser processes (only for Unix-like OS).
    -h --help                   Show this screen.
    --version                   Show version.
```

When you run tool without any options for the first time, it will ask you to create credentials file in `~/.tgeraser` directory. You can specify your own path to credentials file with `-i` option. Session files will be stored in the same directory.

**Note:**
- TgEraser uses YAML format for credentials file by default
- To use environment variables to specify credentials, you need to have pre-created session file
- You can specify credentials in JSON format with `-j` option, data must be escaped with double quotes and structured like YAML credentials file
- Example of credentials file in YAML format here: [credentials.yml](./examples/credentials.yml)
