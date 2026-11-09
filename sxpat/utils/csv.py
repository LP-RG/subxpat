from typing import Any, Callable, Iterable
from sxpat.utils.typing import SupportsWrite

from io import StringIO
from _csv import Writer


class CsvFormatter:
    """
        UNUSED

        :authors: Marco Biasion
    """

    def __init__(
        self,
        make_writer: Callable[[SupportsWrite[str]], Writer],
    ) -> None:
        self._buffer = StringIO()
        self._writer = make_writer(self._buffer)

    def format_row(self, row: Iterable[Any]) -> str:
        self._writer.writerow(row)
        formatted = self._buffer.getvalue()
        self._buffer.seek(0)
        self._buffer.truncate(0)
        return formatted

    def format_rows(self, rows: Iterable[Iterable[Any]]) -> Iterable[str]:
        return (self.format_row(row) for row in rows)
