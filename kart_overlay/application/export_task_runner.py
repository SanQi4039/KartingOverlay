from threading import Event

from PySide6.QtCore import QObject, QThread, Signal, Slot

from kart_overlay.application.export_events import ExportCancelledError, ExportTaskRequest


class _ExportWorker(QObject):
    progress = Signal(object)
    finished = Signal(object)
    failed = Signal(str, object)
    cancelled = Signal(str, object)
    done = Signal()

    def __init__(self, *, export_service, request: ExportTaskRequest, cancel_event: Event) -> None:
        super().__init__()
        self._export_service = export_service
        self._request = request
        self._cancel_event = cancel_event

    @Slot()
    def run(self) -> None:
        try:
            result = self._export_service.execute_export(
                telemetry=self._request.telemetry,
                widgets=self._request.widgets,
                canvas_size=self._request.canvas_size,
                fps=self._request.fps,
                duration_sec=self._request.duration_sec,
                start_data_time_sec=self._request.start_data_time_sec,
                output_path=self._request.output_path,
                manifest_path=self._request.manifest_path,
                log_path=self._request.log_path,
                manifest_payload=self._request.manifest_payload,
                export_format=self._request.export_format,
                progress_callback=self.progress.emit,
                cancel_event=self._cancel_event,
            )
        except ExportCancelledError as exc:
            self.cancelled.emit(str(exc), self._request.log_path)
        except Exception as exc:
            self.failed.emit(str(exc), self._request.log_path)
        else:
            self.finished.emit(result)
        finally:
            self.done.emit()


class BackgroundExportTaskRunner(QObject):
    def __init__(self, *, export_service) -> None:
        super().__init__()
        self._export_service = export_service
        self._thread: QThread | None = None
        self._worker: _ExportWorker | None = None
        self._cancel_event: Event | None = None

    def start(self, request: ExportTaskRequest, *, on_progress, on_finished, on_failed, on_cancelled) -> None:
        if self.is_running:
            raise RuntimeError("An export task is already running.")

        self._cancel_event = Event()
        self._thread = QThread()
        self._worker = _ExportWorker(
            export_service=self._export_service,
            request=request,
            cancel_event=self._cancel_event,
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(on_progress)
        self._worker.finished.connect(on_finished)
        self._worker.failed.connect(on_failed)
        self._worker.cancelled.connect(on_cancelled)
        self._worker.done.connect(self._thread.quit)
        self._worker.done.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._cleanup)
        self._thread.start()

    @property
    def is_running(self) -> bool:
        return self._thread is not None

    def cancel(self) -> None:
        if self._cancel_event is not None:
            self._cancel_event.set()

    def _cleanup(self) -> None:
        self._thread = None
        self._worker = None
        self._cancel_event = None
