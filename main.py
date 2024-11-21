""" Tool for checking spelling of USFM files """

# Standard imports
from argparse import ArgumentParser, Namespace
import logging
import sys

# Third party imports
from PySide6.QtWidgets import (
    QApplication,
)

# Project imports
from main_window import MainWindow
import settings


def parse_args() -> Namespace:  # pragma: no cover
    """Parse command line arguments"""
    parser = ArgumentParser(
        description="App to check the spelling of directories of USFM files"
    )
    parser.add_argument("--trace", action="store_true", help="Enable tracing output")
    return parser.parse_args()


def setup_logging(trace: bool) -> None:  # pragma: no cover
    """Setup logging for script."""
    # read logging level from args
    if trace:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.WARNING
    # Set up logging format
    logging.basicConfig(
        format=(
            # Timestamp
            "%(asctime)s "
            # Severity of log entry
            "%(levelname)s "
            # Process and thread
            "%(process)d/%(threadName)s "
            # module/function:line:
            "%(module)s/%(funcName)s:%(lineno)d: "
            # message
            "%(message)s"
        ),
        level=logging_level,
    )


def main() -> None:  # pragma: no cover
    """Main function"""
    args = parse_args()
    setup_logging(args.trace)

    app_settings = settings.load_settings()
    app = QApplication(sys.argv)
    window = MainWindow(app_settings)
    window.show()
    app.exec()
    settings.save_settings(app_settings)


if __name__ == "__main__":  # pragma: no cover
    main()
