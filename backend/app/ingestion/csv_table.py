import csv
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.ingestion.errors import DataValidationError


@dataclass(frozen=True, slots=True)
class CsvRow:
    source: str
    line: int
    values: dict[str, str]

    @property
    def where(self) -> str:
        return f"{self.source} line {self.line}"

    def decimal(self, column: str) -> Decimal:
        text = self.values[column]
        try:
            value = Decimal(text)
        except InvalidOperation:
            raise DataValidationError(
                f"{self.where}: column {column!r} is not a number: {text!r}"
            ) from None
        if not value.is_finite() or value < 0:
            raise DataValidationError(
                f"{self.where}: column {column!r} must be a non-negative number: {text!r}"
            )
        return value

    def integer(self, column: str) -> int:
        text = self.values[column]
        if not text.isascii() or not text.isdigit():
            raise DataValidationError(
                f"{self.where}: column {column!r} is not a whole number: {text!r}"
            )
        return int(text)

    def code(self, column: str) -> str:
        """A source code kept as a string so leading zeros are preserved."""
        text = self.values[column]
        if not text.isascii() or not text.isdigit():
            raise DataValidationError(
                f"{self.where}: column {column!r} must contain digits only: {text!r}"
            )
        return text


def read_csv_rows(path: Path, required_columns: Sequence[str]) -> Iterator[CsvRow]:
    """Yield rows of a UTF-8 (BOM allowed) CSV file, validated against the required columns.

    Values are kept as stripped strings. Missing columns, ragged rows and empty required cells
    raise DataValidationError naming the file, line and column.
    """
    source = path.name
    try:
        handle = path.open(encoding="utf-8-sig", newline="")
    except FileNotFoundError:
        raise DataValidationError(f"{source}: file not found") from None
    with handle:
        reader = csv.reader(handle)
        try:
            first = next(reader, None)
            if first is None:
                raise DataValidationError(f"{source}: file is empty")
            header = [name.strip() for name in first]
            if len(set(header)) != len(header):
                raise DataValidationError(f"{source}: duplicate column names in header")
            missing = [column for column in required_columns if column not in header]
            if missing:
                raise DataValidationError(f"{source}: missing columns: {missing}")
            positions = {column: header.index(column) for column in required_columns}
            for cells in reader:
                if not cells:
                    continue
                line = reader.line_num
                if len(cells) != len(header):
                    raise DataValidationError(
                        f"{source} line {line}: expected {len(header)} fields, found {len(cells)}"
                    )
                values = {column: cells[pos].strip() for column, pos in positions.items()}
                for column, value in values.items():
                    if not value:
                        raise DataValidationError(
                            f"{source} line {line}: empty value in column {column!r}"
                        )
                yield CsvRow(source=source, line=line, values=values)
        except UnicodeDecodeError:
            raise DataValidationError(f"{source}: file is not valid UTF-8") from None
