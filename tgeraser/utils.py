# coding=utf-8
"""
small Python functions and classes which make common patterns shorter and easier
"""
import json
import os
import re
from typing import Any, Dict, Iterable, List, Optional, Set, Union

import yaml

from .exceptions import TgEraserException

_ = Any, Dict, Iterable, List, Optional, Set, Union


def chunks(l: List[Any], n: int) -> Iterable[Any]:
    """Splits list l into chunks of size n. Returns generator"""
    for i in range(0, len(l), n):
        yield l[i : i + n]


def print_header(text: str) -> None:
    """Just for nice output"""
    print("--------------------")
    print(f"| {text} |")
    print("--------------------")


def check_num(name: str, num: int) -> None:
    """check if a string represents an int"""
    try:
        int(num)
    except ValueError:
        raise TgEraserException(f"Error: '{name}' should be integer.")


def get_credentials_from_yaml(
    path: str = None, session_name: str = None
) -> Dict[str, str]:
    """
    Returns credentials and certain session from YAML file
    """
    path_to_file = os.path.abspath(os.path.expanduser(path))
    path_to_directory = os.path.dirname(path)

    if not os.path.exists(path_to_file):
        answer = None
        while answer not in ("yes", "no", "y", "n"):
            answer = input("Do you want create file? (y/n): ").lower()
            if answer in ("yes", "y"):
                create_credential_file(path_to_file, path_to_directory)
            elif answer in ("no", "n"):
                exit(1)
            else:
                print("Please enter yes or no.")

    creds = yaml.load(open(path_to_file, "r"))
    check_credentials_dict(creds)

    if session_name:
        for i, cred in enumerate(creds["sessions"]):
            if cred["session_name"] == session_name:
                creds["sessions"][i]["session_name"] = (
                    os.path.expanduser(path_to_directory) + session_name + ".session"
                )
                return {**creds["api_credentials"], **creds["sessions"][i]}

        raise TgEraserException(
            "It can't find '{0}' session in credentials file.".format(session_name)
        )
    else:
        s = ""
        for i, cred in enumerate(creds["sessions"]):
            s += "{0}. {1}\t | {2}\n".format(
                i, cred["session_name"], cred["user_phone"]
            )

        print(s)
        num = int(input("Choose session: "))
        print("Chosen: " + creds["sessions"][num]["session_name"])

        creds["sessions"][num]["session_name"] = (
            os.path.expanduser("~/.tgeraser/")
            + creds["sessions"][num]["session_name"]
            + ".session"
        )
        return {**creds["api_credentials"], **creds["sessions"][num]}


def create_credential_file(path: str, directory: str):
    """
    creates credential YAML file
    """
    os.makedirs(directory, exist_ok=True)

    phone_pattern = re.compile(r"^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$")
    credentials = {"api_credentials": {}, "sessions": [{}]}

    credentials["api_credentials"]["api_id"] = input("Enter api_id: ")
    credentials["api_credentials"]["api_hash"] = input("Enter api_hash: ")

    credentials["sessions"][0]["session_name"] = input("Enter session_name: ")
    credentials["sessions"][0]["user_phone"] = input("Enter user_phone (+1234567890): ")

    i: int = 0
    while not phone_pattern.search(credentials["sessions"][0]["user_phone"]):
        i += 1
        if i == 4:
            raise TgEraserException("Incorrect phone number. Exiting...")

        print("Incorrect phone number. Try again.")
        credentials["sessions"][0]["user_phone"] = input(
            "Enter user_phone (+1234567890): "
        )

    with open(path, "w") as yaml_file:
        yaml.dump(credentials, yaml_file, default_flow_style=False)

    print(f"Credentials file is created ({path}).")

    return {**credentials["api_credentials"], **credentials["sessions"][0]}


def get_credentials_from_json(json_str: str) -> Dict[str, str]:
    """
    Returns credentials and certain session from JSON string
    """
    creds = json.loads(json_str)
    check_credentials_dict(creds)
    return creds


def check_credentials_dict(creds: Dict[str, str]) -> None:
    """Checks basic structure of credentials dictionary"""
    if not creds["api_credentials"]:
        raise TgEraserException("Credentials file doesn't contain 'api_credentials'.")
    if not creds["api_credentials"]["api_id"]:
        raise TgEraserException("Credentials file doesn't contain 'api_id'.")
    if not creds["api_credentials"]["api_hash"]:
        raise TgEraserException("Credentials file doesn't contain 'api_hash'.")
    if not creds["sessions"]:
        raise TgEraserException("Credentials file doesn't contain sessions.")
