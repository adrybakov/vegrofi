import os
from argparse import ArgumentParser
from math import sqrt


def convert_comment(o_file, comment_lines):
    o_file.write("=" * 80 + "\n")
    for line in comment_lines:
        words = line.split()

        if (
            len(words) == 2
            and words[0].lower() == "grogu"
            and words[1].lower() == "notation"
        ):
            o_file.write("=" * 80 + "\n")
            o_file.write(
                "Hamiltonian convention\n"
                "Double counting      true\n"
                "Normalized spins     true\n"
                "Intra-atomic factor  +1\n"
                "Exchange factor      +0.5\n"
            )
            break

        o_file.write(line)


def convert_cell(o_file, cell_lines):
    o_file.write("=" * 80 + "\n")
    o_file.write("Cell (Ang)\n")
    for line in cell_lines[1:]:
        words = line.split()
        if len(words) == 3:
            o_file.write(line)


def convert_atoms(o_file, atoms_lines):
    o_file.write("=" * 80 + "\n")
    o_file.write("Magnetic sites\n")
    magnetic_sites = []
    for line in atoms_lines[2:]:
        words = line.split()

        if len(words) == 14:
            spin_vector = list(map(float, words[5:8]))
            spin_value = sqrt(
                spin_vector[0] ** 2 + spin_vector[1] ** 2 + spin_vector[2] ** 2
            )

            spin_vector = [tmp / spin_value for tmp in spin_vector]

            magnetic_sites.append(
                f"{words[0]:<5} "
                f"{float(words[1]):>8.4f} "
                f"{float(words[2]):>8.4f} "
                f"{float(words[3]):>8.4f} "
                f"{spin_value:>8.4f} "
                f"{spin_vector[0]:>8.4f} "
                f"{spin_vector[1]:>8.4f} "
                f"{spin_vector[2]:>8.4f}"
            )
    o_file.write(f"Number of sites {len(magnetic_sites)}\n")
    o_file.write(
        "Name   x (Ang)  y (Ang)  z (Ang)        s       sx       sy       sz\n"
    )
    o_file.write("\n".join(magnetic_sites) + "\n")


def convert_intra(o_file, intra_lines):
    o_file.write("=" * 80 + "\n")
    o_file.write("Intra-atomic anisotropy tensor (meV)\n")

    intra_parameters = []
    for i, line in enumerate(intra_lines):
        words = line.split()

        if len(words) == 1 and words[0].lower() == "matrix":
            o_file.write("-" * 36 + "\n")
            o_file.write("".join(intra_lines[i - 1 : i + 4]))

    o_file.write("-" * 36 + "\n")


def convert_exchange(o_file, exchange_lines):
    o_file.write("=" * 80 + "\n")
    o_file.write("Exchange tensor (meV)\n")

    exchange_parameters = []
    for i, line in enumerate(exchange_lines):
        words = line.split()

        if len(words) == 1 and words[0].lower() == "matrix":
            exchange_parameters.append("".join(exchange_lines[i - 1 : i + 4]))

    o_file.write(f"Number of pairs {len(exchange_parameters)}\n")
    o_file.write("-" * 41 + "\n")
    o_file.write("Name1   Name2      i   j   k      d (Ang)\n")
    for parameter in exchange_parameters:
        o_file.write("-" * 41 + "\n")
        o_file.write(parameter)

    o_file.write("-" * 41 + "\n")


def convert(filename: str):
    print(f"Converting {filename} ...")

    head, tail = os.path.split(filename)

    o_filename = os.path.join(head, f"converted_{tail}")

    o_file = open(o_filename, "w")
    with open(filename, "r") as f:
        lines = f.readlines()

    comment_lines = []
    cell_lines = []
    atoms_lines = []
    exchange_lines = []
    intra_lines = []
    i = 0

    lines_containers = [
        comment_lines,
        cell_lines,
        atoms_lines,
        exchange_lines,
        intra_lines,
    ]
    j = -1
    while i < len(lines):
        if "=" * 20 in lines[i]:
            j += 1
            i += 1
            continue

        lines_containers[j].append(lines[i])
        i += 1

    # Process comments
    convert_comment(o_file=o_file, comment_lines=comment_lines)

    # Process cell
    convert_cell(o_file=o_file, cell_lines=cell_lines)

    # Process atoms
    convert_atoms(o_file=o_file, atoms_lines=atoms_lines)

    # Process intra
    convert_intra(o_file=o_file, intra_lines=intra_lines)

    # Process exchange
    convert_exchange(o_file=o_file, exchange_lines=exchange_lines)

    # Close the file
    o_file.write("=" * 80 + "\n")
    o_file.close()

    print(f"Done, result saved in\n  {os.path.abspath(o_filename)}")


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "filenames",
        type=str,
        nargs="+",
        help="One or more filenames that will be converted.",
    )

    filenames = parser.parse_args().filenames

    for filename in filenames:
        convert(filename=filename)
