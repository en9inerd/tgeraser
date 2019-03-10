# coding=utf-8
"""
Stop gap build script until I find something better.
"""
import glob
import json
import os
import subprocess
import sys
from json import JSONDecodeError

from pynt import task
from pyntcontrib import execute, safe_cd
from semantic_version import Version

PROJECT_NAME = "tgeraser"
SRC = "."
PYTHON = "python"
IS_DJANGO = False
IS_TRAVIS = "TRAVIS" in os.environ  # I double we will ever use travis...
if IS_TRAVIS:
    PIPENV = ""
else:
    PIPENV = "pipenv run"

CURRENT_HASH = None

MAC_LIBS = ":"

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
from build_utils import (
    check_is_aws,
    execute_get_text,
    execute_with_environment,
    skip_if_no_change,
    timed,
)


@task()
@timed()
def clean_state():
    with safe_cd(".build_state"):
        # wild cards don't expand by default
        for file in os.listdir("."):
            if file.startswith("last") and file.endswith(".txt"):
                execute("rm", "-f", str(file))


@task()
@timed()
def update_pip_and_pipenv():
    # env = config_pythonpath()
    execute("pip", "install", "--upgrade", "pip")


@task()
@timed()
def clean():
    pass


@task()
@skip_if_no_change("formatting")
def formatting():
    with safe_cd(SRC):
        if sys.version_info < (3, 6):
            print("Black doesn't work for current version of Python")
            return
        command = "{0} black {1}".format(PIPENV, PROJECT_NAME).strip()
        print(command)
        result = execute_get_text(command)
        assert result
        changed = []
        for line in result.split("\n"):
            if "reformatted " in line:
                file = line[len("reformatted ") :].strip()
                changed.append(file)
        for change in changed:
            command = "git add {0}".format(change)
            print(command)
            execute(*(command.split(" ")))


@task(clean, formatting)
@skip_if_no_change("compile_py")
@timed()
def compile_py():
    with safe_cd(SRC):
        execute(PYTHON, "-m", "compileall", PROJECT_NAME)


@task(compile_py)
@timed()
def prospector():
    with safe_cd(SRC):
        execute(
            "pipenv",
            *(
                "run prospector {0} --profile tgeraser_style --pylint-config-file=pylintrc.ini --profile-path=.prospector".format(
                    PROJECT_NAME
                ).split(
                    " "
                )
            )
        )


@task(compile_py, prospector)
@skip_if_no_change("lint")
def lint():
    """
    Lint
    """
    with safe_cd(SRC):
        if os.path.isfile("lint.txt"):
            execute("rm", "lint.txt")

    with safe_cd(SRC):
        if IS_DJANGO:
            django_bits = "--load-plugins pylint_django "
        else:
            django_bits = ""

        # command += "{0}--rcfile=pylintrc.ini {1}".format(django_bits, PROJECT_NAME).split(" ")
        command = (
            "{0} pylint {1} --rcfile=pylintrc.ini {2}".format(
                PIPENV, django_bits, PROJECT_NAME
            )
            .strip()
            .replace("  ", " ")
        )
        print(command)
        command = command.split(" ")

        # keep out of src tree, causes extraneous change detections
        lint_output_file_name = "lint.txt"
        with open(lint_output_file_name, "w") as outfile:
            env = config_pythonpath()
            subprocess.call(command, stdout=outfile, env=env)

        fatal_errors = sum(
            1
            for line in open(lint_output_file_name)
            if "no-member" in line
            or "no-name-in-module" in line
            or "import-error" in line
        )

        if fatal_errors > 0:
            for line in open(lint_output_file_name):
                if (
                    "no-member" in line
                    or "no-name-in-module" in line
                    or "import-error" in line
                ):
                    print(line)

            print("Fatal lint errors : {0}".format(fatal_errors))
            exit(-1)

        cutoff = 100
        num_lines = sum(
            1
            for line in open(lint_output_file_name)
            if "*************" not in line
            and "---------------------" not in line
            and "Your code has been rated at" not in line
        )
        if num_lines > cutoff:
            raise TypeError(
                "Too many lines of lint : {0}, max {1}".format(num_lines, cutoff)
            )


@task(lint)
@timed()
def nose_tests():
    with safe_cd(SRC):
        if IS_DJANGO:
            # Django app
            command = "{0} {1} manage.py test {2} -v 2".format(
                PIPENV, PYTHON, PROJECT_NAME
            ).strip()
            # We'd expect this to be MAC or a build server.
            my_env = config_pythonpath()
            execute_with_environment(command, env=my_env)
        else:
            my_env = config_pythonpath()
            if IS_TRAVIS:
                command = "{0} -m nose {1}".format(PYTHON, "test").strip()
            else:
                command = "{0} {1} -m nose {2}".format(PIPENV, PYTHON, "test").strip()
            print(command)
            execute_with_environment(command, env=my_env)


def config_pythonpath():
    """
    Add to PYTHONPATH
    """
    if check_is_aws():
        env = "DEV"
    else:
        env = "MAC"
    my_env = {"ENV": env}
    for key, value in os.environ.items():
        my_env[key] = value
    my_env["PYTHONPATH"] = my_env.get("PYTHONPATH", "") + MAC_LIBS
    print(my_env["PYTHONPATH"])
    return my_env


@task()
@skip_if_no_change("vulture", expect_files="dead_code.txt")
@timed()
def dead_code():
    """
    This also finds code you are working on today!
    """
    with safe_cd(SRC):
        exclusions = "--exclude *settings.py,migrations/,*models.py,*_fake.py,*tests.py,*ui/admin.py"
        if IS_TRAVIS:
            command = (
                "{0} vulture {1} {2}".format(PYTHON, PROJECT_NAME, exclusions)
                .strip()
                .split()
            )
        else:
            command = (
                "{0} vulture {1} {2}".format(PIPENV, PROJECT_NAME, exclusions)
                .strip()
                .split()
            )

        output_file_name = "dead_code.txt"
        with open(output_file_name, "w") as outfile:
            env = config_pythonpath()
            subprocess.call(command, stdout=outfile, env=env)

        cutoff = 120
        num_lines = sum(1 for line in open(output_file_name) if line)
        if num_lines > cutoff:
            print(
                "Too many lines of dead code : {0}, max {1}".format(num_lines, cutoff)
            )
            exit(-1)


@task()
@timed()
def coverage():
    """
    Do tests exercise enough code?
    """
    print("Coverage tests always re-run")
    with safe_cd(SRC):
        my_env = config_pythonpath()
        # You will need something like this in pytest.ini
        # By default, pytest is VERY restrictive in the file names it will match.
        #
        # [pytest]
        # DJANGO_SETTINGS_MODULE = core.settings
        # python_files = tests.py test_*.py *_tests.py test*_*.py *_test*.py
        if not os.path.exists("pytest.ini") and IS_DJANGO:
            print(
                "pytest.ini MUST exist for Django test detection or too few tests are found."
            )
            exit(-1)
            return

        my_env = config_pythonpath()
        command = "{0} py.test {1} --cov={2} --cov-report html:coverage --cov-fail-under 55  --verbose".format(
            PIPENV, "test", PROJECT_NAME
        )
        execute_with_environment(command, my_env)


@task()
@timed()
def pip_check():
    """
    Are packages ok?
    """
    execute("pip", "check")
    if PIPENV and not IS_TRAVIS:
        execute("pipenv", "check")
    execute("safety", "check", "-r", "requirements_dev.txt")


@task()
@skip_if_no_change("mypy")
def mypy():
    """
    Are types ok?
    """
    if sys.version_info < (3, 4):
        print("Mypy doesn't work on python < 3.4")
        return
    if IS_TRAVIS:
        command = "{0} -m mypy {1} --ignore-missing-imports --strict".format(
            PYTHON, PROJECT_NAME
        ).strip()
    else:
        command = "{0} mypy {1} --ignore-missing-imports --strict".format(
            PIPENV, PROJECT_NAME
        ).strip()

    bash_process = subprocess.Popen(
        command.split(" "),
        # shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = bash_process.communicate()  # wait
    mypy_file = "mypy_errors.txt"
    with open(mypy_file, "w+") as lint_file:
        lines = out.decode().split("\n")
        for line in lines:
            if "build_utils.py" in line:
                continue
            if "test.py" in line:
                continue
            if "tests.py" in line:
                continue
            if "/test_" in line:
                continue
            if "/tests_" in line:
                continue
            else:
                lint_file.writelines([line + "\n"])

    num_lines = sum(1 for line in open(mypy_file) if line and line.strip(" \n"))
    max_lines = 25
    if num_lines > max_lines:
        raise TypeError(
            "Too many lines of mypy : {0}, max {1}".format(num_lines, max_lines)
        )


@task()
@skip_if_no_change("detect_secrets", expect_files="detect-secrets-results.txt")
@timed()
def detect_secrets():
    # skipo for the moment.
    pass
    # use
    # blah blah = "foo"     # pragma: whitelist secret
    # to ignore a false posites
    errors_file = "detect-secrets-results.txt"

    command = "detect-secrets scan --base64-limit 4 --exclude .idea|lock.json|lint.txt|{0}".format(
        errors_file
    )
    print(command)
    bash_process = subprocess.Popen(
        command.split(" "),
        # shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out = bash_process.communicate()[0]  # wait

    with open(errors_file, "w+") as file_handle:
        result = out.decode()
        if not result:
            print("Failed, no detect secrets results.")
            # exit(-1)
        file_handle.write(result)

    try:
        with open(errors_file) as f:
            data = json.load(f)

        if data["results"]:
            for result in data["results"]:
                print(result)
                print(
                    "detect-secrets has discovered high entropy strings, possibly passwords?"
                )
                exit(-1)
    except JSONDecodeError:
        pass


@task()
@timed()
def compile_md():
    with safe_cd(SRC):
        execute(
            "pandoc",
            *("--from=markdown --to=rst --output=README.rst README.md".split(" "))
        )


@task()
@timed()
def jiggle_version():
    with safe_cd(SRC):
        command = "pip install jiggle_version --upgrade"
        execute(*(command.split(" ")))
        command = "{0} jiggle_version here --module={1}".format(
            PIPENV, PROJECT_NAME
        ).strip()
        result = execute_get_text(command)
        print(result)
        command = "{0} jiggle_version find --module={1}".format(
            PIPENV, PROJECT_NAME
        ).strip()
        result = execute_get_text(command)
        print(result)


@task()
@timed()
def pin_dependencies():
    """
    Create requirement*.txt
    """
    with safe_cd(SRC):
        execute(*("{0} pipenv_to_requirements".format(PIPENV).strip().split(" ")))


@task(compile_md)
@timed()
def check_setup_py():
    """
    Setup.py checks package things including README.rst
    """
    with safe_cd(SRC):
        if IS_TRAVIS:
            execute(PYTHON, *("setup.py check -r -s".split(" ")))
        else:
            execute(
                *(
                    "{0} {1} setup.py check -r -s".format(PIPENV, PYTHON)
                    .strip()
                    .split(" ")
                )
            )


@task(
    # pin_dependencies,
    dead_code,
    check_setup_py,
    compile_md,
    compile_py,
    mypy,
    lint,
    # coverage,
    nose_tests,
    jiggle_version,
    detect_secrets,
)
@skip_if_no_change("package")
@timed()
def package():
    with safe_cd(SRC):
        for folder in ["build", "dist", PROJECT_NAME + ".egg-info"]:
            execute("rm", "-rf", folder)

    with safe_cd(SRC):
        execute(PYTHON, "setup.py", "sdist", "--formats=gztar,zip")

    os.system('say "package complete."')


@task()
@skip_if_no_change("upload_package")
@timed()
def upload_package():
    """
    Upload
    """
    with safe_cd(SRC):
        if IS_TRAVIS:
            pass
        else:
            execute(
                *("{0} {1} setup.py upload".format(PIPENV, PYTHON).strip().split(" "))
            )


@task()
@timed()
def echo(*args, **kwargs):
    """
    Pure diagnotics
    """
    print(args)
    print(kwargs)


# Default task (if specified) is run when no task is specified in the command line
# make sure you define the variable __DEFAULT__ after the task is defined
# A good convention is to define it at the end of the module
# __DEFAULT__ is an optional member

__DEFAULT__ = echo
