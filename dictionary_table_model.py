""" Maps a dictionary of WordEntries to back a table. """

# Standard imports
from typing import Any, Optional

# Third party imports
from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    QSortFilterProxyModel,
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


class FilterProxyModel(QSortFilterProxyModel):
    """Model for filtering the table"""

    def __init__(self) -> None:
        super().__init__()
        self.filter_text = ""

    def set_filter_text(self, text: str) -> None:
        """Set the filter text"""
        self.filter_text = text.lower()
        self.invalidateFilter()  # Triggers the filter to be reapplied

    # Override the filterAcceptsRow method to filter based on column 1
    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex
    ) -> bool:
        """Filter out rows that don't match filter"""
        index = self.sourceModel().index(source_row, 0, source_parent)  # Column 1
        column_text = str(self.sourceModel().data(index)).lower()
        return self.filter_text in column_text
