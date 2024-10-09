""" TODO: Purpose of this program """

# Standard imports
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Optional
import logging
import subprocess
import sys

# Third party imports
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QTableView,
    QHBoxLayout,
    QSizePolicy,
    QTextEdit,
    QMessageBox,
    QInputDialog,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
    QSortFilterProxyModel,
    QModelIndex,
    QPersistentModelIndex,
)

# Project imports
from main_window import MainWindow
import analyzer


def parse_args() -> Namespace:  # pragma: no cover
    """Parse command line arguments"""
    parser = ArgumentParser(description="TODO: Description of this script")
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
            # module/function:line:
            "%(module)s/%(funcName)s:%(lineno)d: "
            # message
            "%(message)s"
        ),
        level=logging_level,
    )


class DictionaryTableModel(QAbstractTableModel):
    """Provides a data model that maps WordEntries to a table"""

    def __init__(self, data_dict: dict[str, analyzer.WordEntry]):
        super().__init__()
        self.data_dict = data_dict
        self.keys = list(self.data_dict.keys())
        self.columns = ["Word", "Count"]

    def rowCount(
        self, parent: Optional[QModelIndex | QPersistentModelIndex] = None
    ) -> int:  # pylint: disable=unused-argument
        return len(self.data_dict)

    def columnCount(
        self, parent: Optional[QModelIndex | QPersistentModelIndex] = None
    ) -> int:  # pylint: disable=unused-argument
        return len(self.columns)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            key = self.keys[index.row()]
            if index.column() == 0:  # First column displays keys
                return key
            if index.column() == 1:  # Second column displays values
                return len(self.data_dict[key].refs)
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.columns[section]
            return str(section)
        return None


def main() -> None:  # pragma: no cover
    """Main function"""
    args = parse_args()
    setup_logging(args.trace)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":  # pragma: no cover
    main()
