# Git Repository Scan

## Goal

This package scans a git repository for files that could potentially contain data.

## Usage

To scan a git repository in the current working directory, type:

```shell
git-scan
```

To scan a repository in another directory, type:

```shell
git-scan -r <repository folder>
```

To get more verbose output, set the logging level with:

```shell
git scan -l debug
```

## Installation

To use the tool, simply install it into your current Python environment:

```shell
pip install git+https://github.com/LFKoning/git-scan
```


## Maintainers

1. Lukas Koning (lfkoning@gmail.com)