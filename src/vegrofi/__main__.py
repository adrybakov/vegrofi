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
import sys
from argparse import ArgumentParser

from termcolor import colored, cprint

from vegrofi import __release_date__, __version__


class FileIsNotValid(Exception):
    def __init__(self, message):
        super().__init__(message)


def check_convention(lines, i, error_messages):
    if len(lines) <= i + 4:
        error_messages.append(
            f"Expected  four lines after the line {i+1}, "
            f"got {len(lines) - i - 1} before the end of file."
        )
        return i

    i += 1
    line = lines[i].split()
    if (
        len(line) < 3
        or line[0].lower() != "double"
        or line[1].lower() != "counting"
        or line[2].lower() != "true"
    ):
        error_messages.append(
            f'Line {i+1}: Expected "Double counting true" (with at least one space '
            f'between each pair of words), got "{lines[i]}".'
        )

    i += 1
    line = lines[i].split()
    if (
        len(line) < 3
        or line[0].lower() != "normalized"
        or line[1].lower() != "spins"
        or line[2].lower() != "true"
    ):
        error_messages.append(
            f'Line {i+1}: Expected "Normalized spins true" (with at least one space '
            f'between each pair of words), got "{lines[i]}".'
        )

    i += 1
    line = lines[i].split()
    if (
        len(line) < 3
        or line[0].lower() != "intra-atomic"
        or line[1].lower() != "factor"
        or line[2].lower() != "+1"
    ):
        error_messages.append(
            f'Line {i+1}: Expected "Intra-atomic factor +1" (with at least one space '
            f'between each pair of words), got "{lines[i]}".'
        )

    i += 1
    line = lines[i].split()
    if (
        len(line) < 3
        or line[0].lower() != "exchange"
        or line[1].lower() != "factor"
        or line[2].lower() != "+0.5"
    ):
        error_messages.append(
            f'Line {i+1}: Expected "Exchange factor +0.5" (with at least one space '
            f'between each pair of words), got "{lines[i]}".'
        )

    return i


def check_cell(lines, i, error_messages):
    if len(lines) <= i + 3:
        error_messages.append(
            f"Expected three lines after the line {i+1}, "
            f"got {len(lines) - i - 1} before the end of file."
        )
        return i

    for _ in range(3):
        i += 1
        line = lines[i].split()
        if len(line) < 3:
            error_messages.append(
                f"Line {i+1}: Expected three numbers separated by at least one space "
                f'symbol, got "{lines[i]}".'
            )

        try:
            a = list(map(float, line[:3]))
        except:
            error_messages.append(
                f'Line {i+1}: Expected three numbers convertable to floats, got "{lines[i]}".'
            )

    return i


def check_magnetic_sites(lines, i, error_messages):
    i_zero = i

    if len(lines) <= i + 2:
        error_messages.append(
            f"Expected at least two lines after the line {i+1}, "
            f"got {len(lines) - i - 1} before the end of file."
        )
        return i, None

    i += 1
    line = lines[i].split()
    M = None
    if (
        len(line) < 4
        or line[0].lower() != "number"
        or line[1].lower() != "of"
        or line[2].lower() != "sites"
    ):
        error_messages.append(
            f'Line {i+1}: Expected "Number of sites" followed by a single integer '
            f'(with at least one space between each pair of words), got "{lines[i]}".'
        )
    else:
        try:
            M = int(line[3])
        except:
            error_messages.append(
                f'Line {i+1}: Expected "Number of sites" followed by a single integer '
                f'(with at least one space between each pair of words), got "{lines[i]}".'
            )

    i += 1
    line = lines[i].split()
    if (
        len(line) < 11
        or line[0].lower() != "name"
        or line[1].lower() != "x"
        or line[2].lower() != "(ang)"
        or line[3].lower() != "y"
        or line[4].lower() != "(ang)"
        or line[5].lower() != "z"
        or line[6].lower() != "(ang)"
        or line[7].lower() != "s"
        or line[8].lower() != "sx"
        or line[9].lower() != "sy"
        or line[10].lower() != "sz"
    ):
        error_messages.append(
            f'Line {i+1}: Expected "Name x (Ang) y (Ang) z (Ang) s sx sy sz" '
            f'(with at least one space between each pair of words), got "{lines[i]}".'
        )

    if M is None:
        return i, None
    elif len(lines) <= i + M:
        error_messages.append(
            f"Expected at least {M} lines after the line {i+1}, "
            f"got {len(lines) - i - 1} before the end of file."
        )
        return i, None

    names = []
    for _ in range(M):
        i += 1
        line = lines[i].split()
        if len(line) < 8:
            error_messages.append(
                f"Line {i+1}: Expected one string and seven numbers, separated by at "
                f'least one space symbol, got "{lines[i]}".'
            )
        else:
            names.append(line[0])
            try:
                for j in range(1, 8):
                    float(line[j])
            except:
                error_messages.append(
                    f"Line {i+1}: Expected one string and seven numbers, separated by at "
                    f'least one space symbol, got "{lines[i]}".'
                )
    if len(names) != M:
        return i, None

    if len(names) != len(set(names)):
        error_messages.append(
            f"Lines {i_zero+1}-{i+1}: Names of the magnetic sites are not unique."
        )
    return i, names


def check_file(filename):
    error_messages = []
    found_convention = False
    found_cell = False
    found_sites = False
    found_intra_atomic = False
    found_exchange = False

    with open(filename, "r") as f:
        lines = f.readlines()

    i = 0
    names = None
    while i < len(lines):
        if "Hamiltonian convention" in lines[i]:
            found_convention = True
            i = check_convention(i=i, lines=lines, error_messages=error_messages)

        if "Cell (Ang)" in lines[i]:
            found_cell = True
            i = check_cell(i=i, lines=lines, error_messages=error_messages)

        if "Magnetic sites" in lines[i]:
            found_sites = True
            i, names = check_magnetic_sites(
                i=i, lines=lines, error_messages=error_messages
            )
        if "Intra-atomic anisotropy tensor (meV)" in lines[i]:
            found_intra_atomic = True
        if "Exchange tensor (meV)" in lines[i]:
            found_exchange = True

        i += 1

    if not found_convention:
        error_messages.append("Section with the convention is not found.")
    if not found_cell:
        error_messages.append("Section with the unit cell is not found.")
    if not found_sites:
        error_messages.append("Section with the magnetic sites is not found.")
    if not found_intra_atomic:
        error_messages.append(
            "Section with the intra-atomic anisotropy parameters is not found."
        )
    if not found_exchange:
        error_messages.append("Section with the exchange parameters is not found.")

    return error_messages


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "filename", type=str, help="File with spin Hamiltonian produced by GROGU."
    )

    logo = [
        "  ██╗   ██╗███████╗ ██████╗ ██████╗  ██████╗ ███████╗██╗",
        "  ██║   ██║██╔════╝██╔════╝ ██╔══██╗██╔═══██╗██╔════╝██║",
        "  ██║   ██║█████╗  ██║  ███╗██████╔╝██║   ██║█████╗  ██║",
        "  ╚██╗ ██╔╝██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝  ██║",
        "   ╚████╔╝ ███████╗╚██████╔╝██║  ██║╚██████╔╝██║     ██║",
        "    ╚═══╝  ╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝",
        " " * 46 + "▄   ▄     ",
        f"{f'Version: {__version__}':^46}" + "█▀█▀█     ",
        f"{f'Relese date: {__release_date__}':^46}" + "█▄█▄█     ",
        f"{'License: MIT license':^46}" + " ███   ▄▄ ",
        f"{'Copyright (C): 2025 Andrey Rybakov':^46}" + " ████ █  █",
        " " * 46 + " ████    █",
        " " * 46 + " ▀▀▀▀▀▀▀▀ ",
    ]
    print("\n".join(logo))

    filename = parser.parse_args().filename

    if not os.path.isfile(filename):
        cprint(f"File {os.path.abspath(filename)} not found.", color="red")
        sys.exit(1)

    print(f'Checking a file "{os.path.abspath(filename)}"')

    error_messages = check_file(filename=filename)

    if len(error_messages) == 0:
        cprint("It is a valid GROGU file.", color="green")
    else:
        cprint("\n".join(error_messages), color="red")
        sys.tracebacklimit = 0
        raise FileIsNotValid("It is NOT a valid GROGU file.")


if __name__ == "__main__":
    main()
