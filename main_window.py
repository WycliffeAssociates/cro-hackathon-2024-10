""" Main window of app """

# Standard imports
from pathlib import Path
import logging
import subprocess
from typing import cast, Any, Tuple

# Third party imports
from pygit2 import Repository, Signature
from PySide6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QStatusBar,
    QLineEdit,
    QDockWidget,
    QHeaderView,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import (
    Qt,
    QModelIndex,
    QThreadPool,
)

# Project imports
from analyzer import WordEntry
from dictionary_table_model import DictionaryTableModel
from filter_proxy_model import FilterProxyModel
import analyzer
from worker import Worker


class MainWindow(QMainWindow):
    """Main Window"""

    def __init__(self) -> None:
        """Initialize main window."""
        super().__init__()
        self.setWindowTitle("Spell Checking App")
        self.setWindowIcon(QIcon("icon.png"))

        # Threading
        self.threadpool = QThreadPool()

        # Data
        self.path = Path("/home/oliverc/repos/en_ulb_craig")
        self.word_entries: dict[str, analyzer.WordEntry] = {}

        # Load USFM button
        self.load_usfm_button = QPushButton("Load USFM")
        self.load_usfm_button.clicked.connect(self.on_load_usfm_clicked)

        # Filter field
        filter_field = QLineEdit()
        filter_field.setPlaceholderText("Filter word list")
        filter_field.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        )
        filter_field.textChanged.connect(self.on_filter_changed)

        # Table of words
        table_model = DictionaryTableModel({})
        self.table_view = QTableView()
        self.table_view.setModel(table_model)
        self.table_view.setSortingEnabled(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )
        self.table_view.clicked.connect(self.on_table_cell_clicked)
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        # List of references
        self.references = QTextEdit()
        self.references.setReadOnly(True)

        # Fix Spelling button
        fix_spelling_button = QPushButton("Fix Spelling")
        fix_spelling_button.clicked.connect(self.on_fix_spelling_clicked)

        # Push Changes button
        push_changes_button = QPushButton("Push changes")
        push_changes_button.clicked.connect(self.on_push_changes_clicked)

        # Create left pane layout
        left_pane_layout = QVBoxLayout()
        left_pane_layout.addWidget(self.load_usfm_button)
        left_pane_layout.addWidget(filter_field)
        left_pane_layout.addWidget(self.table_view)
        left_pane_layout.addWidget(fix_spelling_button)
        left_pane_layout.addWidget(push_changes_button)

        # Status bar
        self.setStatusBar(QStatusBar())

        # Setup left dock
        left_dock_widget = QWidget()
        left_dock_widget.setLayout(left_pane_layout)
        left_dock = QDockWidget(self)
        left_dock.setWidget(left_dock_widget)
        left_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)

        # Setup main window
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)
        self.setCentralWidget(self.references)
        self.resize(800, 600)

    def on_load_usfm_clicked(self) -> None:
        """Load a USFM file or directory."""

        # Ask user for directory
        directory = QFileDialog.getExistingDirectory(
            self, "Select USFM Directory", dir=str(self.path)
        )

        # Abort if canceled
        if not directory:
            return

        self.path = Path(directory)

        # Launch worker
        worker = Worker(self.worker_parse_usfm, self.path)
        worker.signals.progress.connect(self.on_worker_progress_update)
        worker.signals.result.connect(self.on_load_usfm_complete)
        self.threadpool.start(worker)
        self.update_status_bar("Reading USFM files...")

    def on_load_usfm_complete(self, word_entries: dict[str, WordEntry]) -> None:
        """Called back on the main thread after USFM parsing is complete."""

        # Remember word entries for later
        self.word_entries = word_entries

        # Update data model
        table_model = DictionaryTableModel(word_entries)
        proxy_table_model = FilterProxyModel()
        proxy_table_model.setSourceModel(table_model)
        proxy_table_model.sort(1, order=Qt.SortOrder.DescendingOrder)

        # Attach data model to table
        self.table_view.setModel(proxy_table_model)

        # Done
        self.update_status_bar("Finished loading USFM.")

    def on_filter_changed(self, text: str) -> None:
        """When the user changes the word filter."""
        proxy_table_model = cast(FilterProxyModel, self.table_view.model())
        proxy_table_model.set_filter_text(text)

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
            text=word,
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

    def on_worker_progress_update(self, percent_complete: int, message: str) -> None:
        """Updates status bar with progress."""
        self.update_status_bar(f"{message} ({percent_complete}%)")

    def on_worker_error(self, error: Tuple[Any, Any, Any]) -> None:
        """Updates status bar with error."""
        logging.error(error[1])
        self.update_status_bar(f"Error: {error[1]}")

    def update_status_bar(self, message: str) -> None:
        """Updates status bar.  Only call on main thread!"""
        logging.debug(message)
        self.statusBar().showMessage(message, 10000)

    def on_push_changes_clicked(self) -> None:
        """Click: Push changes to server."""
        # Launch worker
        worker = Worker(self.worker_push_to_server, self.path)
        worker.signals.progress.connect(self.on_worker_progress_update)
        worker.signals.error.connect(self.on_worker_error)
        self.threadpool.start(worker)

    def worker_parse_usfm(self, *args: Any, **kwargs: Any) -> dict[str, WordEntry]:
        # pylint: disable=unused-argument
        """Analyze USFM."""
        return analyzer.process_file_or_dir(self.path)

    def worker_push_to_server(self, *args: Any, **kwargs: Any) -> None:
        # pylint: disable=unused-argument
        """Push changes to the server."""

        # Setup
        progress_callback = kwargs["progress_callback"]
        repo_dir = str(self.path)
        repo = Repository(repo_dir)

        # Stage files
        progress_callback.emit(0, "Staging files...")
        index = repo.index
        index.add_all()
        index.write()

        # Commit files
        progress_callback.emit(30, "Creating commit...")
        tree_oid = index.write_tree()
        head_ref = repo.head
        parent_commit = repo[head_ref.target]
        parents = [parent_commit.id]
        author = Signature("Unknown", "unknown@example.com")
        committer = author
        message = "Correct spelling"
        commit_oid = repo.create_commit(
            "HEAD",
            author,
            committer,
            message,
            tree_oid,
            parents
        )

        # progress_callback.emit(66, "Pushing files...")
        # command = ["git", "push"]
        # result = subprocess.run(
        #     command, capture_output=True, text=True, cwd=repo_dir, check=True
        # )
        # logging.debug("%s: rc=%d", " ".join(command), result.returncode)

        progress_callback.emit(100, "Done pushing to server.")
