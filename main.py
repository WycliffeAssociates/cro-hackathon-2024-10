""" TODO: Purpose of this program """

# Standard imports
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any
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
)

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
    """Provides a data model that maps WordEntries to a table"""

    def __init__(self, data_dict: dict[str, analyzer.WordEntry]):
        super().__init__()
        self.data_dict = data_dict
        self.keys = list(self.data_dict.keys())
        self.columns = ["Word", "Count"]

    def rowCount(self, parent=None) -> int:  # pylint: disable=unused-argument
        return len(self.data_dict)

    def columnCount(self, parent=None) -> int:  # pylint: disable=unused-argument
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

        # Data
        self.path = Path("/home/oliverc/repos/en_ulb_craig")
        self.word_entries: dict[str, analyzer.WordEntry] = {}

        # Load USFM button
        self.load_usfm_button = QPushButton("Load USFM")
        self.load_usfm_button.clicked.connect(self.on_load_usfm)

        # Table of words
        table_model = DictionaryTableModel({})
        self.table_view = QTableView()
        self.table_view.setModel(table_model)
        self.table_view.setSortingEnabled(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        )
        self.table_view.clicked.connect(self.on_table_cell_clicked)

        # List of references
        self.references = QTextEdit()
        self.references.setReadOnly(True)

        # Fix Spelling button
        self.fix_spelling_button = QPushButton("Fix Spelling")
        self.fix_spelling_button.clicked.connect(self.on_fix_spelling_clicked)

        # Create left pane layout
        left_pane_layout = QVBoxLayout()
        left_pane_layout.addWidget(self.load_usfm_button)
        left_pane_layout.addWidget(self.table_view)
        left_pane_layout.addWidget(self.fix_spelling_button)

        # Create horizontal panes layout
        horizontal_panes_layout = QHBoxLayout()
        horizontal_panes_layout.addLayout(left_pane_layout)
        horizontal_panes_layout.addWidget(self.references)

        # Create central widget
        central_widget = QWidget(self)
        central_widget.setLayout(horizontal_panes_layout)

        self.setCentralWidget(central_widget)
        self.resize(800, 600)

    def on_load_usfm(self) -> None:
        """Load a USFM file or directory."""

        # Ask user for directory
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select USFM Directory",
            dir=str(self.path)
        )

        # Abort if canceled
        if not directory:
            return

        self.path = Path(directory)

        # To do: Run this in a thread so we don't block the UI
        self.word_entries = analyzer.process_file_or_dir(self.path)

        # Update data model
        table_model = DictionaryTableModel(self.word_entries)
        proxy_table_model = QSortFilterProxyModel()
        proxy_table_model.setSourceModel(table_model)
        proxy_table_model.sort(1, order=Qt.DescendingOrder)
        self.table_view.setModel(proxy_table_model)

    def on_table_cell_clicked(self, index: QModelIndex):
        """When the user clicks a cell, show its references"""
        row = index.row()
        word = self.table_view.model().index(row, 0).data()
        self.table_view.selectRow(row)
        word_entry = self.word_entries[word]
        html_refs = []
        for ref in word_entry.refs:
            text = (
                f"<h4>{ref.book} {ref.chapter}:{ref.verse}</h4>"
                f"<p>{ref.text.replace(word, f"<font color='red'>{word}</font>")}</p>"
            )
            html_refs.append(text)
        self.references.setHtml("".join(html_refs))

    def on_fix_spelling_clicked(self) -> None:
        """Fix spelling of selected word."""
        selected_indexes = self.table_view.selectedIndexes()
        if not selected_indexes:
            error_dialog = QMessageBox()
            error_dialog.warning(
                None, "Select Word", "Please select a word to correct."
            )
            error_dialog.setFixedSize(500, 200)
            return
        row = selected_indexes[0].row()
        word = self.table_view.model().index(row, 0).data()
        corrected_spelling, ok = QInputDialog.getText(
            None,
            "Correct Spelling",
            f"Please provide the correct spelling of the word '{word}'",
        )
        if not ok or not corrected_spelling:
            return
        word_entry = self.word_entries[word]
        for ref in word_entry.refs:
            command = ["sed", "-i", f"s/{word}/{corrected_spelling}/g", str(ref.file_path)]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                logging.debug("Success: %s", str(command))
            else:
                logging.warning("Return code %i: %s", result.returncode, str(command))



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
