""" Main window of app """

# Standard imports
from pathlib import Path
import logging
import subprocess

# Third party imports
from PySide6.QtWidgets import (
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
    QSortFilterProxyModel,
    QModelIndex,
)

# Project imports
from analyzer import WordEntry
from dictionary_table_model import DictionaryTableModel
import analyzer


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

        # Fix Spelling button
        self.push_changes_button = QPushButton("Push changes")
        self.push_changes_button.clicked.connect(self.on_push_changes_clicked)

        # Create left pane layout
        left_pane_layout = QVBoxLayout()
        left_pane_layout.addWidget(self.load_usfm_button)
        left_pane_layout.addWidget(self.table_view)
        left_pane_layout.addWidget(self.fix_spelling_button)
        left_pane_layout.addWidget(self.push_changes_button)

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
            self, "Select USFM Directory", dir=str(self.path)
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
        proxy_table_model.sort(1, order=Qt.SortOrder.DescendingOrder)
        self.table_view.setModel(proxy_table_model)

    def on_table_cell_clicked(self, index: QModelIndex) -> None:
        """When the user clicks a cell, show its references"""
        row = index.row()
        word = self.table_view.model().index(row, 0).data()
        self.table_view.selectRow(row)
        word_entry = self.word_entries[word]
        self.build_refs(word_entry)

    def on_fix_spelling_clicked(self) -> None:
        """Fix spelling of selected word."""
        selected_indexes = self.table_view.selectedIndexes()
        if not selected_indexes:
            error_dialog = QMessageBox()
            error_dialog.warning(
                self, "Select Word", "Please select a word to correct."
            )
            error_dialog.setFixedSize(500, 200)
            return
        row = selected_indexes[0].row()
        word = self.table_view.model().index(row, 0).data()
        corrected_spelling, ok = QInputDialog.getText(
            self,
            "Correct Spelling",
            f"Please provide the correct spelling of the word '{word}'",
        )
        if not ok or not corrected_spelling:
            return
        word_entry = self.word_entries[word]
        for ref in word_entry.refs:
            command = [
                "sed",
                "-i",
                f"s/{word}/{corrected_spelling}/g",
                str(ref.file_path),
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            if result.returncode != 0:
                logging.warning("Return code %i: %s", result.returncode, str(command))
                return
            logging.debug("Success: %s", str(command))
            ref.text = ref.text.replace(word, corrected_spelling)
        self.build_refs(word_entry)

    def build_refs(self, word_entry: WordEntry) -> None:
        """Build HTML reference text display."""
        html_refs = []
        for ref in word_entry.refs:
            highlighted_text = ref.text.replace(
                word_entry.word, f"<font color='red'>{word_entry.word}</font>"
            )
            text = (
                f"<h4>{ref.book} {ref.chapter}:{ref.verse}</h4>"
                f"<p>{highlighted_text}</p>"
            )
            html_refs.append(text)
        self.references.setHtml("".join(html_refs))

    def on_push_changes_clicked(self) -> None:
        """Push changes to server."""

        repo_dir = str(self.path)

        command = ["git", "add", "--all"]
        result = subprocess.run(
            command, capture_output=True, text=True, cwd=repo_dir, check=True
        )
        if result.returncode != 0:
            logging.warning("Return code %i: %s", result.returncode, str(command))
            return
        logging.debug("Success: %s", str(command))
        logging.debug("%s", result.stdout)
        logging.debug("%s", result.stderr)

        command = ["git", "commit", "-m", "Correct spelling"]
        result = subprocess.run(
            command, capture_output=True, text=True, cwd=repo_dir, check=True
        )
        if result.returncode != 0:
            logging.warning("Return code %i: %s", result.returncode, str(command))
            return
        logging.debug("Success: %s", str(command))
        logging.debug("%s", result.stdout)
        logging.debug("%s", result.stderr)

        command = ["git", "push"]
        result = subprocess.run(
            command, capture_output=True, text=True, cwd=repo_dir, check=True
        )
        if result.returncode != 0:
            logging.warning("Return code %i: %s", result.returncode, str(command))
            return
        logging.debug("Success: %s", str(command))
        logging.debug("%s", result.stdout)
        logging.debug("%s", result.stderr)
