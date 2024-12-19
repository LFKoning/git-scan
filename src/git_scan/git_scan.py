"""Scan a git repo for data files."""

import argparse
import logging
import pathlib
import subprocess

# File extensions that might contain data.
EXTENSIONS = ["csv", "ipynb", "parquet", "pbix", "tsv", "xls", "xlsx", "xlsb", "xml"]

logger = logging.getLogger("GitScanner")


def get_arguments():
    """Get command line arguments."""
    parser = argparse.ArgumentParser("Git repo scanner.")
    parser.add_argument("-r", "--repo", help="Path to the repository.", default=".")
    parser.add_argument(
        "-l",
        "--loglevel",
        help="Logging level.",
        choices={"debug", "info", "warning", "error", "critical"},
        default="info",
    )
    return parser.parse_args()


def scan_tree(tree_hash: str, repo_path: pathlib.Path) -> list:
    """Get file paths that may contain data."""
    logger.debug("Processing tree: %s", tree_hash)
    git_pipe = subprocess.PIPE

    try:
        result = subprocess.run(
            ["git", "cat-file", "-p", tree_hash],
            stdout=git_pipe,
            stderr=git_pipe,
            universal_newlines=True,
            check=True,
            cwd=repo_path,
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError("Cannot read tree objects {tree_hash}") from error

    data_files = []
    for line in result.stdout.split("\n"):
        for extension in EXTENSIONS:
            if line.endswith(extension):
                filename = line.split()[-1]
                data_files.append(filename)
                break

    logger.debug("Found %d data files.", len(data_files))
    return data_files


def get_trees(repo_path: pathlib.Path) -> list:
    """Get tree objects from git objects."""
    logger.info("Listing tree objects.")
    git_pipe = subprocess.PIPE

    result = None
    try:
        result = subprocess.run(
            ["git", "cat-file", "--batch-check", "--batch-all-objects"],
            stdout=git_pipe,
            stderr=git_pipe,
            universal_newlines=True,
            check=True,
            cwd=repo_path,
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError("Cannot list trees objects form the repository") from error

    trees = []
    for line in result.stdout.split("\n"):
        if "tree" in line:
            ohash = line.split()[0]
            trees.append(ohash)

    logger.info("Found %d trees.", len(trees))
    return trees


def main():
    """Main program routine."""
    args = get_arguments()
    logging.basicConfig(
        level=args.loglevel.upper(),
        format="%(asctime)s - %(levelname)-8s - %(name)-20s %(message)-.150s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )
    logger.setLevel(args.loglevel.upper())

    logger.info("Starting repository scan.")
    repo_path = pathlib.Path(args.repo)

    tree_objects = get_trees(repo_path)

    logger.info("Scanning trees for data files.")
    data_files = []
    for tree_object in tree_objects:
        data_files.extend(scan_tree(tree_object, repo_path))

    # Convert to set to remove duplicates.
    data_files = set(data_files)
    logger.info("Found %d data files.", len(data_files))
    logger.info("Finished scanning.")

    print("\n\n")
    print("-" * 21)
    print("Potential data files:")
    print("-" * 21)
    for data_file in data_files:
        print(data_file)


if __name__ == "__main__":
    main()
