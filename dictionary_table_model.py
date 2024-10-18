""" Maps a dictionary of WordEntries to back a table. """

# Standard imports
from typing import Any, Optional

# Third party imports
from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
)

# Project imports
from analyzer import WordEntry


class DictionaryTableModel(QAbstractTableModel):
    """Provides a data model that maps WordEntries to a table"""

    def __init__(self, data_dict: dict[str, WordEntry]):
        super().__init__()
        self.data_dict = data_dict
        self.keys = list(self.data_dict.keys())
        self.columns = ["Word", "Count"]

    # pylint: disable=unused-argument
    def rowCount(
        self,
        parent: Optional[QModelIndex | QPersistentModelIndex] = None,
    ) -> int:
        return len(self.data_dict)

    # pylint: disable=unused-argument
    def columnCount(
        self,
        parent: Optional[QModelIndex | QPersistentModelIndex] = None,
    ) -> int:
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
