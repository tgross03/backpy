# backpy [![CI Status](https://github.com/tgross03/backpy/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/tgross03/backpy/actions/workflows/ci.yml?branch=main) [![codecov](https://codecov.io/gh/tgross03/backpy/graph/badge.svg?token=NSQD951ZPJ)](https://codecov.io/gh/tgross03/backpy) [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/tgross03/backpy/main.svg)](https://results.pre-commit.ci/latest/github/tgross03/backpy/main) [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)


[![BackPy Logo](./docs/_static/backpy_logo_dark.png)](https://github.com/tgross03/backpy)

> [!CAUTION]
> This package is still in development and not stable at this time! Features and functionalities might not work as expected.

BackPy is a python-based tool to back up file spaces and SQL-based databases. It features a well-documented Command-Line Interface (CLI)
for the configuration of the software, the creation and management of backup spaces and backups.

## Features

- Manual and scheduled backups for backing up files and directories
- Implementation of remotely saving backups on servers using `scp` or `sftp`
- Crontab based scheduling of automatic backups
- Command-Line Interface (CLI) for full configuration and usage of all functions
- Fully accessible Python API for code-based interactions with the package

## Roadmap

- Documentation for API and CLI (via docstrings and documentation website)
- Introduction of tests and GitHub CI
- Addition of MariaDB / MySQL-database backups
- Addition of encryption for saved backup-archives

## Installation

> [!NOTE]
> Currently only a manual installation using a Python package manager like `pip` is possible.
> We are working on more installation options.

### Manual Installation
For that clone this repository to your local system, navigate to the repositories root directory and execute
```shell
pip install -e .
```

## Usage
> [!NOTE]
> Because of the early development stage, we will be providing more detailed documentation about the usage of the CLI and API.

To interact with backpy open a terminal, activate your environment containing backpy and type
```shell
backpy --help
```
You will be presented with the help overview page of the backpy command. From there you can use the `backpy` command prefix to interact
with the submodules.
