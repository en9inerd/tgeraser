"""
small Python functions and classes which make common patterns shorter and easier
"""
import json
import os
import re
import sys
from typing import Any, Dict, Iterable, List, Optional, Set, Union

import yaml

from .exceptions import TgEraserException

_ = Any, Dict, Iterable, List, Optional, Set, Union


def chunks(input_list: List[Any], num: int) -> Iterable[Any]:
    """Splits list input_list into chunks of size n. Returns generator"""
    for i in range(0, len(input_list), num):
        yield input_list[i : i + num]


def sprint(string: str, *args: Any, **kwargs: Any) -> None:
    """Safe Print (handle UnicodeEncodeErrors on some terminals)"""
    try:
        print(string, *args, **kwargs)
    except UnicodeEncodeError:
        string = string.encode("utf-8", errors="ignore").decode(
            "ascii", errors="ignore"
        )
        print(string, *args, **kwargs)


def print_header(title: str) -> None:
    """Helper function to print titles to the console more nicely"""
    sprint("\n")
    sprint("=={}==".format("=" * len(title)))
    sprint("= {} =".format(title))
    sprint("=={}==".format("=" * len(title)))


def get_env(name: str, message: str, cast: Any = str) -> Any:
    """Helper to get environment variables interactively"""
    if name in os.environ:
        return os.environ[name]
    while True:
        value = input(message)
        try:
            return cast(value)
        except ValueError as err:
            print(err, file=sys.stderr)


def cast_to_int(num: str, name: str) -> int:
    """check if a string represents an int"""
    try:
        return int(num)
    except ValueError as err:
        raise TgEraserException(f"Error: '{name}' should be integer.") from err


def get_credentials(args: Dict[str, Any]) -> Dict[str, str]:
    """Presents credentials dict from specified source"""

    path_to_file = os.path.abspath(os.path.expanduser(args["--input-file"]))
    path_to_directory = os.path.dirname(path_to_file) + "/"
    os.makedirs(path_to_directory, exist_ok=True)

    creds = {}  # type: Dict[str, Any]
    if args["--json"]:
        creds = get_credentials_from_json(
            args["--json"], path_to_directory, args["<session_name>"]
        )
    elif args["--environment-variables"]:
        creds = get_credentials_from_env(path_to_directory)
    else:
        if not os.path.exists(path_to_file):
            answer = None
            while answer not in ("yes", "no", "y", "n"):
                answer = input("Do you want create file? (y/n): ").lower()
                if answer in ("yes", "y"):
                    creds = create_credential_file(path_to_file, path_to_directory)
                elif answer in ("no", "n"):
                    exit(1)
                else:
                    print("Please enter yes or no.")
        else:
            creds = get_credentials_from_yaml(
                path_to_file, path_to_directory, args["<session_name>"]
            )

    return creds


def get_credentials_from_yaml(
    path_to_file: str, path_to_directory: str, session_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Returns credentials and certain session from YAML file
    """
    creds = yaml.load(open(path_to_file, "r"), Loader=yaml.SafeLoader)
    check_credentials_dict(creds)

    if session_name:
        for i, cred in enumerate(creds["sessions"]):
            if cred["session_name"] == session_name:
                creds["sessions"][i]["session_name"] = (
                    path_to_directory + session_name + ".session"
                )
                print("Session file: " + creds["sessions"][i]["session_name"])
                return {**creds["api_credentials"], **creds["sessions"][i]}

        raise TgEraserException(
            f"It can't find '{session_name}' session in credentials file."
        )

    else:
        print_header("Sessions")
        for i, cred in enumerate(creds["sessions"], start=1):
            sprint(
                "{0}. {1}\t | {2}".format(
                    i,
                    cred["session_name"],
                    cred.get("user_phone", "Phone number wasn't specified"),
                )
            )

        num = int(input("\nChoose session: ")) - 1
        print("Chosen: " + creds["sessions"][num]["session_name"] + "\n")

        creds["sessions"][num]["session_name"] = (
            path_to_directory + creds["sessions"][num]["session_name"] + ".session"
        )
        return {**creds["api_credentials"], **creds["sessions"][num]}


def create_credential_file(path: str, directory: str) -> Dict[str, str]:
    """
    creates credential YAML file
    """
    phone_pattern = re.compile(
        r"(([+][(]?[0-9]{1,3}[)]?)|([(]?[0-9]{4}[)]?))"
        r"\s*[)]?[-\s\.]?[(]?[0-9]{1,3}[)]?([-\s\.]?[0-9]{3})"
        r"([-\s\.]?[0-9]{3,4})"
    )
    credentials = {
        "api_credentials": {"api_id": "", "api_hash": ""},
        "sessions": [{"session_name": "", "user_phone": ""}],
    }  # type: Dict[str, Any]

    credentials["api_credentials"]["api_id"] = cast_to_int(
        input("Enter api_id: "), "api_id"
    )
    credentials["api_credentials"]["api_hash"] = input("Enter api_hash: ")

    credentials["sessions"][0]["session_name"] = input("Enter session_name: ")

    i: int = 0
    while True:
        credentials["sessions"][0]["user_phone"] = input(
            "Enter user_phone (+1234567890): "
        )
        if not phone_pattern.search(credentials["sessions"][0]["user_phone"]):
            print("Incorrect phone number. Try again.")
        else:
            break

        i += 1
        if i == 3:
            raise TgEraserException("Incorrect phone number. Exiting...")

    with open(path, "w") as yaml_file:
        yaml.dump(credentials, yaml_file, default_flow_style=False)

    print(f"Credentials file is created ({path}).")

    credentials["sessions"][0]["session_name"] = (
        directory + credentials["sessions"][0]["session_name"] + ".session"
    )

    return {**credentials["api_credentials"], **credentials["sessions"][0]}


def get_credentials_from_json(
    json_str: str, path: str, session_name: str
) -> Dict[str, Any]:
    """
    Returns credentials and certain session from JSON string
    """
    creds = json.loads(json_str)
    check_credentials_dict(creds)

    if session_name:
        for i, cred in enumerate(creds["sessions"]):
            if cred["session_name"] == session_name:
                creds["sessions"][i]["session_name"] = path + session_name + ".session"
                print("Session file: " + creds["sessions"][i]["session_name"])
                return {**creds["api_credentials"], **creds["sessions"][i]}

        raise TgEraserException(
            f"It can't find '{session_name}' session in credentials file."
        )
    else:
        print_header("Sessions")
        for i, cred in enumerate(creds["sessions"], start=1):
            sprint(f"{i}. {cred['session_name']}\t | {cred['user_phone']}")

        num = int(input("\nChoose session: ")) - 1
        print("Chosen: " + creds["sessions"][num]["session_name"] + "\n")

        creds["sessions"][num]["session_name"] = (
            path + creds["sessions"][num]["session_name"] + ".session"
        )
        return {**creds["api_credentials"], **creds["sessions"][num]}


def get_credentials_from_env(path: str) -> Dict[str, Any]:
    """Gets credentials from environment variables"""
    api_id = get_env("TG_API_ID", "Enter your API ID: ", int)
    api_hash = get_env("TG_API_HASH", "Enter your API hash: ")
    session = get_env("TG_SESSION", "Enter session name: ")
    session = path + session + ".session"
    return {"api_id": api_id, "api_hash": api_hash, "session_name": session}


def check_credentials_dict(creds: Dict[str, Any]) -> None:
    """Checks basic structure of credentials dictionary"""
    if not creds["api_credentials"]:
        raise TgEraserException("Credentials file doesn't contain 'api_credentials'.")
    if not creds["api_credentials"]["api_id"]:
        raise TgEraserException("Credentials file doesn't contain 'api_id'.")
    if not creds["api_credentials"]["api_hash"]:
        raise TgEraserException("Credentials file doesn't contain 'api_hash'.")
    if not creds["sessions"]:
        raise TgEraserException("Credentials file doesn't contain sessions.")
    if not creds["sessions"][0]["session_name"]:
        raise TgEraserException("Credentials file doesn't contain session_name.")
