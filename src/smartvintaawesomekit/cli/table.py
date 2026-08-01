"""Table formatter with sorting, filtering, and theme support.

Provides Rich-based table rendering with column sorting, case-insensitive filtering,
DataFrame support, and theme-consistent styling.

Usage:
    from smartvintaawesomekit.cli.table import render_table, display_table

    data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    table_str = render_table(data, title="Users", sort_by="name")
    display_table(data, title="Users")
"""

from __future__ import annotations

from typing import Any

from pydantic_settings import BaseSettings
from rich.console import Console
from rich.table import Table

from smartvintaawesomekit.cli.theme import ThemeConfig


class TableConfig(BaseSettings):
    """Table display configuration.

    Prefix: CLI_TABLE_

    Attributes:
        max_width: Maximum table width in characters (0 = auto).
        sortable: Whether sorting functionality is available.
        filterable: Whether filtering functionality is available.
        show_header: Whether to show column headers.
        row_alternating: Whether to use alternating row colors.
        default_sort_column: Default column to sort by.
        default_sort_reverse: Reverse sort order for default sort.
    """

    max_width: int = 0
    sortable: bool = True
    filterable: bool = True
    show_header: bool = True
    row_alternating: bool = True
    default_sort_column: str | None = None
    default_sort_reverse: bool = False

    model_config = {"env_prefix": "CLI_TABLE_"}


def _get_theme_config(theme: ThemeConfig | None) -> ThemeConfig:
    """Get a ThemeConfig instance, using default if none provided."""
    return theme if theme is not None else ThemeConfig()


def _get_table_config(table_cfg: TableConfig | None) -> TableConfig:
    """Get a TableConfig instance, using default if none provided."""
    return table_cfg if table_cfg is not None else TableConfig()


def render_table(
    data: list[dict[str, Any]],
    *,
    columns: list[str] | None = None,
    title: str | None = None,
    caption: str | None = None,
    max_width: int | None = None,
    sort_by: str | None = None,
    sort_reverse: bool = False,
    filter_by: str | None = None,
    filter_value: str | None = None,
    theme: ThemeConfig | None = None,
) -> str:
    """Render tabular data as a Rich Table string.

    Args:
        data: List of dictionaries representing rows.
        columns: Optional list of column names to include (order preserved).
                 If None, all keys from the first data dict are used.
        title: Optional table title.
        caption: Optional table caption.
        max_width: Maximum table width in characters. Uses TableConfig.max_width if None.
        sort_by: Column name to sort by.
        sort_reverse: If True, sort in descending order.
        filter_by: Column name to filter on.
        filter_value: Value to filter by (case-insensitive substring match).
        theme: Optional ThemeConfig for styling.

    Returns:
        A string containing the rendered Rich Table.

    Example:
        table_str = render_table(
            [{"name": "Alice", "age": 30}],
            title="Users",
            sort_by="name",
        )
        print(table_str)
    """
    tc = _get_theme_config(theme)
    tbl_cfg = TableConfig()
    effective_max_width = max_width if max_width is not None else tbl_cfg.max_width

    # Determine columns
    if columns is None:
        columns = list(data[0].keys()) if data else []

    # Filter data
    filtered_data = data
    if filter_by is not None and filter_value is not None and filter_by in columns:
        filter_lower = filter_value.lower()
        filtered_data = [
            row
            for row in data
            if filter_by in row and isinstance(row[filter_by], str)
            and filter_lower in row[filter_by].lower()
        ]

    # Sort data
    if sort_by is not None and sort_by in columns and tbl_cfg.sortable:
        sorted_data = sorted(
            filtered_data,
            key=lambda row: str(row.get(sort_by, "")),
            reverse=sort_reverse,
        )
    else:
        sorted_data = filtered_data

    # Build Rich Table
    table = Table(
        title=title,
        caption=caption,
        show_header=tbl_cfg.show_header,
        header_style=tc.table_header,
        border_style=tc.table_border,
        row_styles=["", tc.table_alt_rows] if tbl_cfg.row_alternating else None,
        width=effective_max_width if effective_max_width > 0 else None,
    )

    # Add columns
    for col in columns:
        table.add_column(col)

    # Add rows
    for row in sorted_data:
        table.add_row(*[str(row.get(col, "")) for col in columns])

    # Render to string
    console = Console(width=effective_max_width if effective_max_width > 0 else None)
    with console.capture() as capture:
        console.print(table)

    return capture.get()


def display_table(
    data: list[dict[str, Any]],
    *,
    columns: list[str] | None = None,
    title: str | None = None,
    caption: str | None = None,
    sort_by: str | None = None,
    sort_reverse: bool = False,
    theme: ThemeConfig | None = None,
) -> None:
    """Render and print a table to the console.

    Args:
        data: List of dictionaries representing rows.
        columns: Optional list of column names to include.
        title: Optional table title.
        caption: Optional table caption.
        sort_by: Column name to sort by.
        sort_reverse: If True, sort in descending order.
        theme: Optional ThemeConfig for styling.

    Example:
        display_table(
            [{"name": "Alice", "age": 30}],
            title="Users",
            sort_by="name",
        )
    """
    result = render_table(
        data,
        columns=columns,
        title=title,
        caption=caption,
        sort_by=sort_by,
        sort_reverse=sort_reverse,
        theme=theme,
    )
    Console().print(result, end="")


def dataframe_to_table(
    df: Any | None = None,  # noqa: ANN401 — third-party DataFrame type
    *,
    max_rows: int = 50,
    theme: ThemeConfig | None = None,
) -> str:
    """Convert a pandas DataFrame to a Rich table string.

    Args:
        df: A pandas DataFrame, or None (returns empty string).
        max_rows: Maximum number of rows to include (default: 50).
        theme: Optional ThemeConfig for styling.

    Returns:
        A string containing the rendered Rich Table.

    Example:
        import pandas as pd
        df = pd.DataFrame({"name": ["Alice"], "age": [30]})
        table_str = dataframe_to_table(df)
        print(table_str)
    """
    if df is None:
        return ""

    # Convert DataFrame to list of dicts, respecting max_rows
    rows = df.head(max_rows).to_dict(orient="records")

    return render_table(
        rows,
        title=getattr(df, "name", None),
        theme=theme,
    )


__all__ = ["TableConfig", "render_table", "display_table", "dataframe_to_table"]
