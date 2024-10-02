# Python Kickstart Project

This repo provides a basic environment for kickstarting a new Python
project. It has the following features already set up:

-   a virtual environment using `venv`
-   linting using `mypy` and `pylint`
-   testing using `unittest` and `coverage`
-   formatting using `black` and `pandoc`
-   command-line arguments and help using `argparse`
-   logging, including setting debug via `--trace`
-   Setup for running, debugging, and testing via VSCode

# Files

Main files in this project:

-   `main.py`: Your Python source code goes here.
-   `tests/test_main.py`: Your unit tests can go in this directory.
-   `requirements.txt`: Edit to add or remove library dependencies.
-   `makefile`: Contains commands for `make` to execute.

# Make commands

Use `make` to do basic operations:

-   `make run` to run the program.
-   `make run-trace` to run with debug logs sent to stderr.
-   `make lint` to run mypy and pylint on source and tests.
-   `make test` to discover and run tests with coverage.
-   `make format` to reformat Python source files and readme.md.

# Virtual Environment

Virtual environment management is automatic. Update `requirements.txt`
to add or remove libraries, and the makefile commands will automatically
call `venv` and `pip` as needed to update the environment.

# Unit testing

Unit tests, including tests for project modules, can all go in the
`tests/` folder. It is already set up as a importable module for
automatic test discovery.

# VSCode

VSCode has been configured for several actions:

-   Run and debug `main.py` with and without tracing.
-   Discover, run, and debug your unit tests in the "Testing" view.
-   To create or update the virtual environment for VSCode, use
    `make .venv`.

# Troubleshooting

Sometimes VSCode doesn't start correctly the first time when clicking
the "Start Debugging" action from the "Run and Debug" panel. Wait for it
to time out, then try the action again.

If VSCode doesn't seem to be picking up your modules, you may need to
use the command "Python: select interpreter" to select the one in the
project's virtual environment directory: `./.venv/bin/python`

If you need to force an update to the project dependencies, you can
`touch requirements.txt` and then execute any `make` command,
e.g. `make .venv`, to detect the change and update the dependencies.

If you need to force a rebuild of the virtual environment from scratch,
you can delete it using `make clean`, and then execute any `make`
command, e.g. `make .venv`, to re-create the virtual environment.
