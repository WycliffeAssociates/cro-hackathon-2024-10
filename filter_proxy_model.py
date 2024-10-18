""" Table filter model that allows filtering the word text """

# Standard imports

# Third party imports
from PySide6.QtCore import (
    QModelIndex,
    QPersistentModelIndex,
    QSortFilterProxyModel,
)


class FilterProxyModel(QSortFilterProxyModel):
    """Model for filtering the table"""

    def __init__(self) -> None:
        super().__init__()
        self.filter_text = ""

    def set_filter_text(self, text: str) -> None:
        """Set the filter text"""
        self.filter_text = text.lower()
        # Triggers the filter to be reapplied
        self.invalidateFilter()

    # Override the filterAcceptsRow method to filter based on column 1
    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex
    ) -> bool:
        """Filter out rows that don't match filter"""
        index = self.sourceModel().index(source_row, 0, source_parent)  # Column 1
        column_text = str(self.sourceModel().data(index)).lower()
        return self.filter_text in column_text
