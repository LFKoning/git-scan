"""Scan a git repo for data files."""

import argparse
import logging
import pathlib
import subprocess
from collections import defaultdict

from git_scan.commit import Commit
from git_scan.datafile import DataFile

# File extensions that might contain data.
EXTENSIONS = [
    "csv",
    "ipynb",
    "parquet",
    "pbix",
    "pptx",
    "tsv",
    "xls",
    "xlsx",
    "xlsb",
    "xml",
]

logger = logging.getLogger("GitScanner")
tree_cache = {}
files_seen = set()


def get_arguments():
    """Get command line arguments."""
    parser = argparse.ArgumentParser("Git repo scanner.")
    parser.add_argument("-r", "--repo", help="Path to the repository.", default=".")
    parser.add_argument(
        "-o", "--output", help="Output file name.", default="scan-results.csv"
    )
    parser.add_argument(
        "-l",
        "--loglevel",
        help="Logging level.",
        choices={"debug", "info", "warning", "error", "critical"},
        default="info",
    )
    return parser.parse_args()


def scan_files(tree_hash: str, repo_path: pathlib.Path, sub_path: pathlib.Path) -> set:
    """Get file paths that may contain data."""
    logger.debug("Processing tree: %s", tree_hash)

    # Tree was parsed before and has no changes.
    if tree_hash in tree_cache:
        return []

    output = ""
    try:
        git_pipe = subprocess.PIPE
        result = subprocess.run(
            ["git", "cat-file", "-p", tree_hash],
            stdout=git_pipe,
            stderr=git_pipe,
            universal_newlines=True,
            check=True,
            cwd=repo_path,
        )
        output = result.stdout.strip()

    except subprocess.CalledProcessError as error:
        raise RuntimeError("Cannot read tree object: {tree_hash}") from error

    # Find data files in the tree.
    # Recursively handle trees for subfolders.
    data_files = []
    for line in output.split("\n"):
        _, otype, ohash, oname = line.split()

        # Handle subtree.
        if otype == "tree":
            data_files.extend(scan_files(ohash, repo_path, sub_path / oname))

        # Handle file.
        elif otype == "blob":
            blob_id = f"{ohash}_{sub_path}_{oname}"
            if blob_id in files_seen:
                continue

            for extension in EXTENSIONS:
                if line.endswith(extension):
                    data_files.append(DataFile(oname, sub_path, ohash))
                    files_seen.add(blob_id)
                    break

    logger.debug("Found %d data files.", len(data_files))
    tree_cache[tree_hash] = data_files
    return data_files


def parse_commit(commit_hash: str, repo_path: pathlib.Path) -> Commit:
    """Get commit information."""
    logger.debug("Processing commit: %s", commit_hash)

    output = ""
    try:
        git_pipe = subprocess.PIPE
        result = subprocess.run(
            ["git", "cat-file", "-p", commit_hash],
            stdout=git_pipe,
            stderr=git_pipe,
            universal_newlines=True,
            check=True,
            cwd=repo_path,
        )
        output = result.stdout.strip()

    except subprocess.CalledProcessError as error:
        raise RuntimeError("Cannot read tree objects {tree_hash}") from error

    tree_hash = timestamp = timezone = ""
    for line in output.split("\n"):
        if line.startswith("tree"):
            tree_hash = line.split()[1]

        elif line.startswith("committer"):
            parts = line.split()
            timestamp = parts[-2]
            timezone = parts[-1]

    return Commit(commit_hash, tree_hash, timestamp, timezone)


def get_all_objects(repo_path: pathlib.Path) -> dict:
    """Lists all object in the repository."""
    logger.info("Listing objects in the repository.")
    git_pipe = subprocess.PIPE

    objects = defaultdict(list)
    try:
        result = subprocess.run(
            ["git", "cat-file", "--batch-check", "--batch-all-objects"],
            stdout=git_pipe,
            stderr=git_pipe,
            universal_newlines=True,
            check=True,
            cwd=repo_path,
        )

        for line in result.stdout.strip().split("\n"):
            ohash, otype, _ = line.split()
            objects[otype].append(ohash)

    except subprocess.CalledProcessError as error:
        raise RuntimeError("Cannot list trees objects form the repository") from error

    return objects


def get_commits(repo_objects: dict, repo_path: pathlib.Path) -> None:
    """Get all commit objects from the repository."""
    logger.info("Found %d commits.", len(repo_objects["commit"]))
    commits = []
    for commit_hash in repo_objects["commit"]:
        commits.append(parse_commit(commit_hash, repo_path))

    # Sort by timestamp.
    commits.sort()
    return commits


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

    logger.info("Processing commit objects.")
    repo_objects = get_all_objects(repo_path)
    commits = get_commits(repo_objects, repo_path)

    data_files = {}
    for commit in commits:
        matches = scan_files(commit.tree_hash, repo_path, repo_path)
        if matches:
            data_files[commit] = matches

    # Convert to set to remove duplicates.
    logger.info("Found %d data files.", len(data_files))
    logger.info("Finished scanning.")

    # Write output as CSV.
    with open(args.output, "w", encoding="utf8") as out_file:
        out_file.write("file_path,file_hash,commit_hash,commit_time\n")
        for commit, data_files in data_files.items():
            for dfile in data_files:
                out_file.write(
                    f"{dfile.full_path},{dfile.hash},{commit.hash},{commit.datetime}\n"
                )


if __name__ == "__main__":
    main()
