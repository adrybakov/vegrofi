# Copyright (c) 2025 Andrey Rybakov

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import os
import re
import sys
from argparse import ArgumentParser
from calendar import month_name
from datetime import datetime
from random import randint

import git
from termcolor import colored

N = 60


class ERROR(Exception):
    pass


def envelope(message: str):
    """
    Decorator for printing a message before and "Done" after a function.

    Parameters
    ----------
    message : str
        Message to print before the function.
    """

    def wrapper(func):
        def inner(*args, relax=False, **kwargs):
            print(f"{f'{message}'} ... ")
            errors = func(*args, **kwargs)
            if errors is not None:
                if relax:
                    print(errors)
                else:
                    raise ERROR(errors)
            print(f"{'':=^{N}}")
            return errors is None

        return inner

    return wrapper


@envelope(message="Updating __init__.py")
def update_init(version, root_dir: str):
    """
    Update __init__.py file.

    Change the __git_hash__, __release_date__ and __version__ variables.

    Parameters
    ----------
    version : str
        Target version for the release.
    """
    cd = datetime.now()

    variables = ["__release_date__", "__version__"]
    values = [f"{cd.day} {month_name[cd.month]} {cd.year}", version]
    good = [False, False]
    good_message = {False: "not updated", True: "updated"}

    # Read __init__.py
    init_file_path = os.path.join(root_dir, "src", "vegrofi", "__init__.py")
    init_file = open(init_file_path, "r")
    init_file_content = init_file.readlines()
    init_file.close()

    # Update __init__.py
    for l_i, line in enumerate(init_file_content):
        # Update git hash
        for v_i, variable in enumerate(variables):
            if re.fullmatch(f"{variable}.*\n", line):
                init_file_content[l_i] = f'{variable} = "{values[v_i]}"\n'
                good[v_i] = True

    # Check if all variables were updated
    if not all(good):
        sys.tracebacklimit = 0
        return "".join(
            [
                colored("\nFailed to update some variables in '__init__.py':\n", "red"),
                *[
                    f"    {variables[i]:20} : {good_message[good[i]]}\n"
                    for i in range(len(variables))
                ],
                "Please check the file and try again\n",
            ]
        )

    # Write __init__.py
    init_file = open(init_file_path, "w", encoding="utf-8")
    init_file.writelines(init_file_content)
    init_file.close()


@envelope(message="Checking if everything is committed and pushed")
def check_git_status(repo: git.Repo):
    """
    Check if everything is committed and pushed.

    Parameters
    ----------
    repo : git.Repo
        Git repository object.
    """
    status = repo.git.status()
    if "nothing to commit, working tree clean" not in status:
        sys.tracebacklimit = 0
        return "".join(
            [
                colored("\nThere are uncommitted changes\n", "red"),
                "Please commit them:\n\n",
                status,
            ]
        )
    if (
        "Your branch is up to date with" not in status
        and "HEAD detached at v" not in status
    ):
        sys.tracebacklimit = 0
        return "".join(
            [
                colored("\nThere are unpushed changes\n", "red"),
                "Please push them:\n\n",
                status,
            ]
        )


def main(version: str, root_dir: str, relax: bool = False):
    if version == "None":
        sys.tracebacklimit = 0
        raise ERROR(
            "".join(
                [
                    colored("\nVersion is undefined\n", "red"),
                    "For the make command use the syntax:\n\n",
                    "    make prepare-release VERSION=vx.x.x\n",
                ]
            )
        )
    elif version[0] != "v":
        sys.tracebacklimit = 0
        raise ERROR(colored("\n VERSION should start with lowercase 'v'.", "red"))

    version = version[1:]

    print(f"{'':=^{N}}\n{f'Preparing {version} release':^{N}}\n{'':=^{N}}")
    repo = git.Repo(search_parent_directories=True)

    # rtd - ready to deploy
    rtd = True

    rtd = update_init(version=version, root_dir=root_dir, relax=relax) and rtd

    rtd = check_git_status(repo, relax=relax) and rtd
    if rtd:
        print(colored(f"{f'{version} ready to deploy':^{N}}", "green"))
    else:
        print(colored(f"{f'{version} not ready to deploy':^{N}}", "red"))
    print(f"{'':=^{N}}")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-v",
        "--version",
        metavar="vx.x.x",
        type=str,
        required=True,
        help="Version to release",
    )
    parser.add_argument(
        "-rd",
        "--root-dir",
        metavar="PATH",
        type=str,
        required=True,
        help="Path to the root directory of the project",
    )
    parser.add_argument(
        "-r",
        "--relax",
        action="store_true",
        help="Relax the errors",
    )
    args = parser.parse_args()
    main(**vars(args))
