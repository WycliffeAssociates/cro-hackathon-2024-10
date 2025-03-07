""" Main window of app """

#
# Standard imports
#

from pathlib import Path
import logging
from typing import cast, Any, Tuple

#
# Third party imports
#

# pylint: disable=no-name-in-module
from pygit2 import (
    Repository,
    Signature,
    Oid,
    RemoteCallbacks,
    UserPass,
    GitError,
)
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

#
# Project imports
#

from analyzer import WordEntry
from dictionary_table_model import DictionaryTableModel
from filter_proxy_model import FilterProxyModel
import analyzer
from worker import Worker
from settings import Settings


class MainWindow(QMainWindow):
    # pylint: disable=too-many-instance-attributes, too-many-locals
    """Main Window"""

    def __init__(self, app_settings: Settings) -> None:
        """Initialize main window."""
        super().__init__()

        self.setWindowTitle("Spell Checking App")
        self.setWindowIcon(QIcon("icon.png"))

        # Settings
        self.settings = app_settings
        self.wacs_password = ""

        # Threading
        self.threadpool = QThreadPool()

        # Data
        self.path = Path(self.settings.repo_dir)
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

        # Export Word List button
        self.export_wordlist_button = QPushButton("Export word list")
        self.export_wordlist_button.setEnabled(False)
        self.export_wordlist_button.clicked.connect(self.on_export_wordlist_clicked)

        # Create left pane layout
        left_pane_layout = QVBoxLayout()
        left_pane_layout.addWidget(self.load_usfm_button)
        left_pane_layout.addWidget(filter_field)
        left_pane_layout.addWidget(self.table_view)
        left_pane_layout.addWidget(fix_spelling_button)
        left_pane_layout.addWidget(push_changes_button)
        left_pane_layout.addWidget(self.export_wordlist_button)

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
        # directory = QFileDialog.getExistingDirectory(
        #     self, "Select USFM Directory", dir=str(self.path)
        # )
        dialog = QFileDialog(self, "Select USFM Directory", str(self.path))
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)  # Optional
        if dialog.exec():
            directory = dialog.selectedFiles()[0]
        else:
            return

        self.path = Path(directory)
        self.settings.repo_dir = directory

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

        # Enable export wordlist button
        self.export_wordlist_button.setEnabled(True)

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

    def on_export_wordlist_clicked(self) -> None:
        """Export word list."""
        # Launch worker
        worker = Worker(self.worker_export_wordlist)
        worker.signals.progress.connect(self.on_worker_progress_update)
        worker.signals.error.connect(self.on_worker_error)
        self.threadpool.start(worker)

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

        # Fix in UI
        word_entry = self.word_entries[word]
        for ref in word_entry.refs:
            ref.text = ref.text.replace(word, corrected_spelling)
        self.build_refs(word_entry)

        # Launch worker to fix USFM files
        worker = Worker(
            self.worker_fix_spelling, word=word, corrected_spelling=corrected_spelling
        )
        worker.signals.progress.connect(self.on_worker_progress_update)
        worker.signals.error.connect(self.on_worker_error)
        self.threadpool.start(worker)

    def worker_fix_spelling(self, *args: Any, **kwargs: Any) -> None:
        # pylint: disable=unused-argument
        """Correct spelling in USFM files."""

        # Setup
        progress_callback = kwargs["progress_callback"]
        word: str = kwargs["word"]
        corrected_spelling: str = kwargs["corrected_spelling"]
        logging.debug("Correcting spelling of %s to %s...", word, corrected_spelling)

        # Get refs for word
        word_entry = self.word_entries[word]
        if not word_entry:
            message = f"ERROR: Couldn't find word entry for {word}!"
            logging.error(message)
            progress_callback.emit(100, message)
            return

        # Count files to be corrected
        files_to_be_corrected = []
        for ref in word_entry.refs:
            # Don't correct the same file more than once
            if ref.file_path in files_to_be_corrected:
                continue
            files_to_be_corrected.append(ref.file_path)

        # Correct USFM files
        files_corrected = []
        for ref in word_entry.refs:
            # Don't correct the same file more than once
            if ref.file_path in files_corrected:
                continue
            files_corrected.append(ref.file_path)
            uncorrected_text = ref.file_path.read_text(encoding="utf-8")
            corrected_text = uncorrected_text.replace(word, corrected_spelling)
            with open(ref.file_path, "w", encoding="utf-8") as file:
                file.write(corrected_text)
                percent_done = int(
                    float(len(files_corrected))
                    / float(len(files_to_be_corrected))
                    * 100.0
                )
                message = f"Corrected {ref.file_path.name}"
                logging.debug(message)
                progress_callback.emit(percent_done, message)

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

        # Verify git user name
        if not self.settings.user_name:
            text, ok = QInputDialog.getText(
                self,
                "Enter Name",
                "Please enter a name for the Git commit, e.g. 'John Doe':",
            )
            if ok and text:
                self.settings.user_name = text

        # Verify git email address
        if not self.settings.email:
            text, ok = QInputDialog.getText(
                self,
                "Enter Email",
                "Please enter an email address for the Git commit, e.g. 'john@example.org':",
            )
            if ok and text:
                self.settings.email = text

        # Verify WACS username
        if not self.settings.wacs_user_id:
            text, ok = QInputDialog.getText(
                self,
                "Enter WACS user id",
                "Please enter your user ID for WACS e.g. 'johnd':",
            )
            if ok and text:
                self.settings.wacs_user_id = text

        # Ask for WACS password
        if not self.wacs_password:
            text, ok = QInputDialog.getText(
                self,
                "Enter WACS password",
                "Please enter your password for WACS. (This is not saved anywhere.)",
                echo=QLineEdit.EchoMode.Password,
            )
            if ok and text:
                self.wacs_password = text

        # Abort if no password
        if not self.wacs_password:
            message = "Could not push to WACS: need password"
            logging.error(message)
            self.update_status_bar(message)
            return

        # Launch worker
        worker = Worker(self.worker_push_to_server, self.path)
        worker.signals.progress.connect(self.on_worker_progress_update)
        worker.signals.error.connect(self.on_worker_error)
        self.threadpool.start(worker)

    def worker_export_wordlist(self, *args: Any, **kwargs: Any) -> None:
        # pylint: disable=unused-argument
        """Export word list to disk."""
        progress_callback = kwargs["progress_callback"]
        progress_callback.emit(0, "Exporting word list, please wait...")
        filename = "word_list.csv"
        with open(filename, "w", encoding="utf-8") as outfile:
            outfile.write("Word,Count\n")
            for word in sorted(self.word_entries.keys()):
                word_entry = self.word_entries[word]
                outfile.write(f"{word_entry.word},{len(word_entry.refs)}\n")
        progress_callback.emit(100, f"Done. Word list exported to {filename}")

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
        progress_callback.emit(33, "Creating commit...")
        tree_oid = index.write_tree()
        head_ref = repo.head
        parent_commit = repo[head_ref.target]
        parents: list[str | Oid] = [parent_commit.id]
        author = Signature(self.settings.user_name, self.settings.email)
        committer = author
        message = "Correct spelling"
        repo.create_commit("HEAD", author, committer, message, tree_oid, parents)

        # Push files to server
        progress_callback.emit(66, "Pushing files to server...")
        remote_name = "origin"
        branch_name = "master"
        remote = repo.remotes[remote_name]
        callbacks = RemoteCallbacks(
            credentials=UserPass(self.settings.wacs_user_id, self.wacs_password)
        )
        try:
            remote.push(
                [f"refs/heads/{branch_name}:refs/heads/{branch_name}"],
                callbacks=callbacks,
            )
            logging.info("Successfully pushed %s to %s.", branch_name, remote_name)
            progress_callback.emit(100, "Done pushing to server.")
        except GitError as git_error:
            message = f"ERROR: Failed to push to remote: {git_error}"
            logging.error(message)
            progress_callback.emit(100, message)
