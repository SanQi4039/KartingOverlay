from pathlib import Path
import subprocess
from threading import Event
from time import sleep

from kart_overlay.application.export_events import ExportCancelledError
from kart_overlay.config import ExternalToolsConfig, binary_path_available


class FfmpegExporter:
    def __init__(self, binary_path: str | None = None) -> None:
        self._binary_path = binary_path or ExternalToolsConfig.from_env().ffmpeg_path

    @property
    def binary_path(self) -> str:
        return self._binary_path

    def ensure_available(self) -> None:
        if binary_path_available(self._binary_path):
            return
        raise FileNotFoundError(
            "ffmpeg not found. Set KART_OVERLAY_FFMPEG_PATH or add ffmpeg to PATH."
        )

    def build_mov_prores_command(
        self,
        *,
        canvas_size: tuple[int, int],
        fps: float,
        output_path: Path,
    ) -> list[str]:
        return [
            self._binary_path,
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgba",
            "-s",
            f"{canvas_size[0]}x{canvas_size[1]}",
            "-r",
            str(fps),
            "-i",
            "-",
            "-c:v",
            "prores_ks",
            "-profile:v",
            "4",
            "-pix_fmt",
            "yuva444p10le",
            "-threads",
            "0",
            str(output_path),
        ]

    def run(
        self,
        command: list[str],
        log_path: Path,
        *,
        frame_stream,
        cancel_event: Event | None = None,
    ) -> None:
        self.ensure_available()
        process = subprocess.Popen(
            command,
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            assert process.stdin is not None
            for frame_bytes in frame_stream:
                if cancel_event is not None and cancel_event.is_set():
                    self._cancel_process(process=process, log_path=log_path)
                process.stdin.write(frame_bytes)
            process.stdin.close()
            while process.poll() is None:
                if cancel_event is not None and cancel_event.is_set():
                    self._cancel_process(process=process, log_path=log_path)
                sleep(0.05)
            stdout = b"" if process.stdout is None else process.stdout.read()
            stderr = b"" if process.stderr is None else process.stderr.read()
        except BrokenPipeError:
            if process.stdin is not None and not process.stdin.closed:
                process.stdin.close()
            stdout = b"" if process.stdout is None else process.stdout.read()
            stderr = b"" if process.stderr is None else process.stderr.read()
            raise subprocess.CalledProcessError(
                process.wait(),
                command,
                stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace"),
            )

        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command, stdout_text, stderr_text)
        log_text = "\n".join(
            part for part in [stdout_text, stderr_text] if part
        )
        log_path.write_text(log_text or "ffmpeg completed", encoding="utf-8")

    def _cancel_process(self, *, process: subprocess.Popen, log_path: Path) -> None:
        if process.stdin is not None and not process.stdin.closed:
            process.stdin.close()
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        stdout = b"" if process.stdout is None else process.stdout.read()
        stderr = b"" if process.stderr is None else process.stderr.read()
        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()
        log_text = "\n".join(
            part for part in [stdout_text, stderr_text, "ffmpeg cancelled"] if part
        )
        log_path.write_text(log_text, encoding="utf-8")
        raise ExportCancelledError("Export cancelled during MOV encoding.")
