"""
pynt_contrib utils.
"""
import functools
import os
import socket
import subprocess
import time

from checksumdir import dirhash

PROJECT_NAME = "tgeraser"
SRC = "."
PYTHON = "python"
IS_GITHUB_CI = "GITHUB_ACTIONS" in os.environ
if IS_GITHUB_CI:
    PIPENV = ""
else:
    PIPENV = "pipenv run"


def check_is_aws() -> bool:
    """
    Checks if current machine on aws
    """
    name = socket.getfqdn()
    return "ip-" in name and ".ec2.internal" in name


class BuildState:
    """
    BuildState class
    """

    def __init__(self, what: str, where: str) -> None:
        self.what = what
        self.where = where
        if not os.path.exists(".build_state"):
            os.makedirs(".build_state")
        self.state_file_name = f".build_state/last_change_{what}.txt"

    def remove_state(self) -> None:
        """
        If a task fails, we don't care if it didn't change since last, re-run
        """
        try:
            os.remove(self.state_file_name)
        except OSError:
            pass

    def has_source_code_tree_changed(self) -> bool:
        """
        If a task succeeds & is re-run and didn't change, we might not
        want to re-run it if it depends *only* on source code
        """
        directory = self.where

        # if CURRENT_HASH is None:
        # print("hashing " + directory)
        # print(os.listdir(directory))
        current_hash = dirhash(
            directory,
            "md5",
            ignore_hidden=True,
            # changing these exclusions can cause dirhas to skip EVERYTHING
            # excluded_files=[".coverage", "lint.txt"],
            excluded_extensions=[".pyc"],
        )

        print("Searching " + self.state_file_name)
        if os.path.isfile(self.state_file_name):
            with open(self.state_file_name, "r+") as file:
                last_hash = file.read()
                if last_hash != current_hash:
                    file.seek(0)
                    file.write(current_hash)
                    file.truncate()
                    return True
                else:
                    return False

        # no previous file, by definition not the same.
        with open(self.state_file_name, "w") as file:
            file.write(current_hash)
            return True


def remove_state(what) -> None:
    """
    If a task fails, we don't care if it didn't change since last, re-run
    """
    state = BuildState(what, PROJECT_NAME)
    state.remove_state()


def has_source_code_tree_changed(task_name, expect_file=None):
    """
    """
    if expect_file:
        if os.path.isdir(expect_file) and not os.listdir(expect_file):
            os.path.dirname(expect_file)
            # output folder empty
            return True
        if not os.path.isfile(expect_file):
            # output file gone
            return True
    state = BuildState(task_name, os.path.join(SRC, PROJECT_NAME))
    return state.has_source_code_tree_changed()


def skip_if_no_change(name, expect_files=None):
    """
    """
    def real_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not has_source_code_tree_changed(name, expect_files):
                print("Nothing changed, won't re-" + name)
                return
            try:
                return func(*args, **kwargs)
            except:
                remove_state(name)
                raise

        return wrapper

    return real_decorator


def execute_with_environment(command, env):
    """
    """
    with subprocess.Popen(
        command.strip().replace("  ", " ").split(" "), env=env
    ) as shell_process:
        value = shell_process.communicate()
        if shell_process.returncode != 0:
            print(
                f"Didn't get a zero return code, got : {shell_process.returncode}"
            )
            exit(-1)
        return value


def execute_get_text(command: str) -> str:
    """
    Execute shell command and return stdout txt
    """
    try:
        completed = subprocess.run(
            command,
            check=True,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as cpe:
        print(cpe.output)
        raise
    else:
        return completed.stdout.decode("utf-8") + completed.stderr.decode("utf-8")


def timed():
    """
    This decorator prints the execution time for the decorated function
    """
    def real_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            print(f"{func.__name__} ran in {round(end - start, 2)}s")
            return result

        return wrapper

    return real_decorator
