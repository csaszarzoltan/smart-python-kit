"""Progress bars with task tracking and theme support.

Wraps Rich's progress bar system with a context manager, task tracking,
and a convenience track() function.

Usage:
    from smartvintaawesomekit.cli.progress import ProgressManager, track

    # As context manager
    with ProgressManager() as progress:
        task = progress.add_task("Processing...", total=100)
        for i in range(100):
            progress.advance(task)

    # Standalone track function
    for item in track(range(100), description="Working"):
        process(item)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

from rich.progress import (
    BarColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from smartvintaawesomekit.cli.theme import ThemeConfig

T = TypeVar("T")


class ProgressManager:
    """Context manager for Rich progress bars with task tracking.

    Wraps a Rich Progress instance and provides add_task, advance, update,
    and track methods for convenient progress reporting.
    """

    def __init__(
        self,
        *,
        transient: bool = False,
        auto_refresh: bool = True,
        theme: ThemeConfig | None = None,
    ) -> None:
        """Initialize progress manager.

        Args:
            transient: If True, progress bars disappear after completion.
            auto_refresh: If True, automatically refresh the display.
            theme: Optional ThemeConfig for styling the progress bars.
        """
        self._transient = transient
        self._auto_refresh = auto_refresh
        self._theme = theme
        self._progress: Progress | None = None
        self._tasks: dict[Any, TaskID] = {}

    def _get_progress(self) -> Progress:
        """Get or create the underlying Rich Progress instance."""
        if self._progress is None:
            theme = self._theme or ThemeConfig()
            progress_columns = [
                TextColumn("[progress.description]{task.description}"),
                BarColumn(
                    bar_width=None,
                    style=theme.progress_bar,
                    complete_style=theme.progress_percent,
                ),
                TextColumn(
                    "[progress.percentage]{task.percentage:>3.0f}%",
                    style=theme.progress_percent,
                ),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
            ]
            self._progress = Progress(
                *progress_columns,
                transient=self._transient,
                auto_refresh=self._auto_refresh,
            )
        return self._progress

    def add_task(
        self,
        description: str,
        total: float = 100.0,
        *,
        completed: float = 0.0,
        visible: bool = True,
        **fields: Any,  # noqa: ANN401
    ) -> TaskID:
        """Add a new task to track.

        Args:
            description: Description of the task.
            total: Total number of steps for completion (default: 100).
            completed: Number of steps already completed (default: 0).
            visible: Whether the task is visible in the progress display.
            **fields: Additional fields for the task.

        Returns:
            A TaskID that can be used to reference this task later.
        """
        progress = self._get_progress()
        task_id = progress.add_task(
            description,
            total=total,
            completed=completed,
            visible=visible,
            **fields,
        )
        return task_id

    def advance(
        self,
        task_id: Any,  # noqa: ANN401
        advance: float = 1.0,
    ) -> None:
        """Advance a task by the given amount.

        Args:
            task_id: The TaskID returned by add_task.
            advance: Amount to advance the task's progress (default: 1.0).
        """
        try:
            progress = self._get_progress()
            progress.advance(task_id, advance)
        except KeyError:
            pass

    def update(
        self,
        task_id: Any,  # noqa: ANN401
        *,
        completed: float | None = None,
        description: str | None = None,
        total: float | None = None,
        **fields: Any,  # noqa: ANN401
    ) -> None:
        """Update task progress attributes.

        Args:
            task_id: The TaskID returned by add_task.
            completed: New completed value.
            description: New task description.
            total: New total value.
            **fields: Additional field updates.
        """
        try:
            progress = self._get_progress()
            progress.update(
                task_id,
                completed=completed,
                description=description,
                total=total,
                **fields,
            )
        except KeyError:
            pass

    def start(self) -> None:
        """Enter the progress context (called automatically on __enter__)."""
        progress = self._get_progress()
        progress.start()

    def stop(self) -> None:
        """Exit the progress context (called automatically on __exit__)."""
        if self._progress is not None:
            self._progress.stop()

    def track(
        self,
        sequence: Iterable[T],
        description: str = "Working...",
        total: float | None = None,
        **fields: Any,  # noqa: ANN401
    ) -> Iterator[T]:
        """Wrap an iterable with automatic progress tracking.

        Args:
            sequence: The iterable to track progress over.
            description: Description of the task.
            total: Total number of items (auto-detected if not provided
                   for sequences with __len__).
            **fields: Additional fields.

        Yields:
            Items from the sequence, updating progress after each item.
        """
        progress = self._get_progress()
        yield from progress.track(
            sequence,
            description=description,
            total=total,
            **fields,
        )

    def __enter__(self) -> ProgressManager:
        """Enter context manager — starts progress display."""
        self.start()
        return self

    def __exit__(self, *args: Any) -> None:  # noqa: ANN401
        """Exit context manager — stops progress display."""
        self.stop()


def track(
    sequence: Iterable[T],
    description: str = "Working...",
    *,
    total: float | None = None,
    transient: bool = False,
    theme: ThemeConfig | None = None,
) -> Iterator[T]:
    """Simple top-level function for one-off progress tracking.

    Args:
        sequence: The iterable to track progress over.
        description: Description of the task.
        total: Total number of items (auto-detected for sequences
               with __len__).
        transient: If True, progress bar disappears after completion.
        theme: Optional ThemeConfig for styling.

    Yields:
        Items from the sequence, updating progress after each item.

    Example:
        for item in track(range(50), description="Downloading"):
            download(item)
    """
    with ProgressManager(transient=transient, theme=theme) as pm:
        yield from pm.track(sequence, description=description, total=total)


__all__ = ["ProgressManager", "track"]
