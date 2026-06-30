from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from PyQt6.QtCore import QObject, QThread, pyqtSignal


class _ApiWorker(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(object)

    def __init__(self, fn: Callable[[], Any]):
        super().__init__()
        self._fn = fn

    def run(self) -> None:
        try:
            self.finished.emit(self._fn())
        except Exception as exc:
            self.failed.emit(exc)


def run_api_task(
    fn: Callable[[], Any],
    on_success: Callable[[Any], None],
    on_error: Callable[[Exception], None] | None = None,
) -> QThread:
    """Run a blocking API callable on a background thread."""
    thread = QThread()
    worker = _ApiWorker(fn)
    worker.moveToThread(thread)

    def _cleanup() -> None:
        thread.quit()

    thread.started.connect(worker.run)
    worker.finished.connect(on_success)
    worker.finished.connect(_cleanup)
    worker.failed.connect(lambda exc: on_error(exc) if on_error else None)
    worker.failed.connect(_cleanup)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.start()
    return thread


def run_parallel_api_task(
    fns: list[Callable[[], Any]],
    on_success: Callable[[list[Any]], None],
    on_error: Callable[[Exception], None] | None = None,
) -> QThread:
    """Run multiple API callables concurrently on a background thread."""

    def run() -> list[Any]:
        if not fns:
            return []
        results: list[Any] = [None] * len(fns)
        with ThreadPoolExecutor(max_workers=min(len(fns), 4)) as pool:
            futures = {pool.submit(fn): index for index, fn in enumerate(fns)}
            for future in futures:
                index = futures[future]
                results[index] = future.result()
        return results

    return run_api_task(run, on_success, on_error)
