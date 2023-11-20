import asyncio
import json
import os
import sys
from typing import Any, Dict, Union

from .exceptions import TgEraserException

TG_API_ID = os.environ.get("TG_API_ID")
TG_API_HASH = os.environ.get("TG_API_HASH")


async def async_input(prompt: str) -> str:
    """Non-blocking input"""
    try:
        print(prompt, end="", flush=True)
        return (
            await asyncio.get_running_loop().run_in_executor(None, sys.stdin.readline)
        ).rstrip()
    except Exception as e:
        raise TgEraserException(f"Error in async_input: {e}")


def sprint(string: str, *args: Any, **kwargs: Any) -> None:
    """Safe Print"""
    try:
        print(string, *args, **kwargs)
    except UnicodeEncodeError:
        string = string.encode("utf-8", errors="ignore").decode(
            "ascii", errors="ignore"
        )
        print(string, *args, **kwargs)


def print_header(title: str) -> None:
    """Print titles to the console nicely"""
    sprint(f"\n=={'=' * len(title)}==")
    sprint(f"= {title} =")
    sprint(f"=={'=' * len(title)}==")


def cast_to_int(num: str, name: str) -> int:
    """Check if a string represents an int"""
    try:
        return int(num)
    except ValueError as err:
        raise TgEraserException(f"Error: '{name}' should be an integer.") from err


async def get_credentials(args: Dict[str, Any]) -> Dict[str, Union[str, int]]:
    """
    Get credentials from file or from user input
    """
    path_to_creds_dir = os.path.abspath(os.path.expanduser(args["--directory"]))
    path_to_creds_file = path_to_creds_dir + "/credentials.json"
    os.makedirs(path_to_creds_dir, exist_ok=True)

    creds = {}

    try:
        if os.path.exists(path_to_creds_file):
            with open(path_to_creds_file, "r") as file:
                creds = json.load(file)
        elif TG_API_ID and TG_API_HASH:
            creds["api_id"] = cast_to_int(TG_API_ID, "api_id")
            creds["api_hash"] = TG_API_HASH
        else:
            creds["api_id"] = cast_to_int(
                await async_input("Enter your API ID: "), "api_id"
            )
            creds["api_hash"] = await async_input("Enter your API hash: ")

            save_to_file = await async_input(
                "Do you want to save your credentials to file? [y/n]: "
            )
            if save_to_file.lower() == "y":
                with open(path_to_creds_file, "w") as file:
                    json.dump(creds, file)
                sprint(f"Credentials saved to '{path_to_creds_file}' file.")

        creds["session_name"] = (
            path_to_creds_dir
            + "/"
            + (args["<session_name>"] or await choose_session(path_to_creds_dir))
        )
    except Exception as e:
        raise TgEraserException(f"Error in get_credentials: {e}")

    return creds


async def choose_session(directory: str) -> str:
    """Choose a session or enter a new one"""
    sessions = list_sessions(directory)

    if sessions:
        print_header("Choose one of the following sessions:")
        for i, session in enumerate(sessions):
            print(f"{i + 1}. {session}")
        session_number = cast_to_int(
            await async_input("\nEnter session number: "), "session number"
        )
        return sessions[session_number - 1]
    else:
        return await async_input("Enter session name: ")


def list_sessions(directory: str) -> list[str]:
    """Return file names with '.session' extension in specified directory"""
    return [
        os.path.splitext(file)[0]
        for file in os.listdir(directory)
        if file.endswith(".session")
    ]
