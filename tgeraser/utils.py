# coding=utf-8
"""
small Python functions and classes which make common patterns shorter and easier
"""
import os
from typing import Any, Dict, Iterable, List, Optional, Set, Union

import yaml

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


def get_credentials(path: str = None, session_name: str = None) -> Dict[str, str]:
    """
    Returns credentials and certain session from YAML file by input
    """
    path_to_creds = os.path.expanduser("~/.tgeraser/credentials.yml")
    creds = yaml.load(open(path_to_creds, "r"))
    if session_name:
        for i, cred in enumerate(creds["sessions"]):
            if cred["session_user_id"] == session_name:
                creds["sessions"][i]["session_user_id"] = (
                    os.path.expanduser("~/.tgeraser/") + session_name + ".session"
                )
                return {**creds["api_credentials"], **creds["sessions"][i]}

        exit("You specified wrong session_name: {0}".format(session_name))
    else:
        s = ""
        for i, cred in enumerate(creds["sessions"]):
            s += "{0}. {1}\t | {2}\n".format(
                i, cred["session_user_id"], cred["user_phone"]
            )

        print(s)
        num = int(input("Choose session: "))
        print("Chosen: " + creds["sessions"][num]["session_user_id"])

        creds["sessions"][num]["session_user_id"] = (
            os.path.expanduser("~/.tgeraser/")
            + creds["sessions"][num]["session_user_id"]
            + ".session"
        )
        return {**creds["api_credentials"], **creds["sessions"][num]}
