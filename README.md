# TgEraser

[![PyPI version](https://badge.fury.io/py/tgeraser.svg)](https://badge.fury.io/py/tgeraser)

TgEraser is a Python tool that allows you to delete all your messages from a chat, channel, or conversation on Telegram without requiring admin privileges. Official Telegram clients do not provide a one-click solution to delete all your messages; instead, you have to manually select and delete messages, with a limit of 100 messages per batch. TgEraser solves this problem and offers a convenient way to mass-delete your messages on Telegram.

## Installation

```
pip install tgeraser
tgeraser
```

To use TgEraser, you'll need to provide `api_id` and `api_hash`, which you can obtain from [here](https://my.telegram.org/auth?to=apps).

There are two methods to define `api_id` and `api_hash`:
1. Set them as environment variables (`TG_API_ID` and `TG_API_HASH`).
2. Allow the tool to prompt you for input during execution, with an option to save the credentials in a `credentials.json` file located in the same directory as the sessions (by default, `~/.tgeraser/`).

## Usage

```
TgEraser deletes all your messages from a chat, channel, or conversation on Telegram without requiring admin privileges.

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
```

Executing the tool without options will guide you through the creation of your first user session. After that you can create sessions for multiple users using the `tgeraser session <new_session_name>` command.

## Contributing

If you have any issues or suggestions, please feel free to open an issue or submit a pull request.
