""" TODO: Purpose of this program """

# Standard imports
from argparse import ArgumentParser, Namespace
from pathlib import Path
import logging
import sys
from typing import Any

# Third party imports
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QTableView,
    QSizePolicy,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel

# Project imports
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
    def __init__(self, data_dict: dict[str, analyzer.WordEntry]):
        super().__init__()
        self.data_dict = data_dict
        self.keys = list(self.data_dict.keys())
        self.columns = ["Word", "Count"]

    def rowCount(self, parent=None) -> int:
        return len(self.data_dict)

    def columnCount(self, parent=None) -> int:
        return len(self.columns)

    def data(self, index, role=Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole:
            key = self.keys[index.row()]
            if index.column() == 0:  # First column displays keys
                return key
            if index.column() == 1:  # Second column displays values
                return len(self.data_dict[key].refs)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole) -> str:
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.columns[section]
            return str(section)
        return None


class MainWindow(QMainWindow):
    """Main Window"""

    def __init__(self) -> None:
        """Initialize main window."""
        super().__init__()
        self.setWindowTitle("Spell Checking App")
        self.setWindowIcon(QIcon("icon.png"))

        # Load USFM button
        self.load_usfm_button = QPushButton("Load USFM")
        self.load_usfm_button.clicked.connect(self.load_usfm)

        # Table of words
        table_model = DictionaryTableModel({})
        self.table_view = QTableView()
        self.table_view.setModel(table_model)

        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(self.load_usfm_button)
        layout.addWidget(self.table_view)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)

    def load_usfm(self) -> None:
        """Load a USFM file or directory."""

        # Ask user for directory
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select USFM Directory",
            dir="/home/oliverc/repos/en_ulb_WycliffeAssociates",
        )

        # Abort if canceled
        if not directory:
            return

        path = Path(directory)

        # To do: Run this in a thread so we don't block the UI
        word_entries = analyzer.process_file_or_dir(path)

        # Update data model
        table_model = DictionaryTableModel(word_entries)
        proxy_table_model = QSortFilterProxyModel()
        proxy_table_model.setSourceModel(table_model)
        self.table_view.setModel(proxy_table_model)
        self.table_view.setSortingEnabled(True)
        proxy_table_model.sort(1, order=Qt.DescendingOrder)


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
