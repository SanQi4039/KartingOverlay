from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
from threading import Event
from time import perf_counter, sleep

from kart_overlay.application.export_events import ExportCancelledError
from kart_overlay.application.export_formats import export_format_by_key
from kart_overlay.config import ExternalToolsConfig, binary_path_available


@dataclass(frozen=True)
class FfmpegCapabilities:
    prores_vulkan_available: bool = False


class FfmpegExporter:
    def __init__(self, binary_path: str | None = None) -> None:
        self._binary_path = binary_path or ExternalToolsConfig.from_env().ffmpeg_path
        self._capabilities: FfmpegCapabilities | None = None

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
        capabilities: FfmpegCapabilities | None = None,
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

    def build_command(
        self,
        *,
        export_format: str,
        canvas_size: tuple[int, int],
        fps: float,
        output_path: Path,
        capabilities: FfmpegCapabilities | None = None,
    ) -> list[str]:
        if export_format == "mov_prores_4444":
            return self.build_mov_prores_command(
                canvas_size=canvas_size,
                fps=fps,
                output_path=output_path,
                capabilities=capabilities,
            )
        if export_format == "mov_qtrle_alpha":
            return self.build_mov_qtrle_command(
                canvas_size=canvas_size,
                fps=fps,
                output_path=output_path,
            )
        raise ValueError(f"Unsupported export format: {export_format}")

    def build_mov_qtrle_command(
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
            "qtrle",
            "-pix_fmt",
            "argb",
            str(output_path),
        ]

    def build_webm_vp9_alpha_command(
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
            "-an",
            "-c:v",
            "libvpx-vp9",
            "-pix_fmt",
            "yuva420p",
            "-auto-alt-ref",
            "0",
            "-deadline",
            "good",
            "-cpu-used",
            "4",
            "-crf",
            "32",
            "-b:v",
            "0",
            str(output_path),
        ]

    def describe_encoder(
        self,
        capabilities: FfmpegCapabilities | None = None,
        *,
        export_format: str = "mov_prores_4444",
    ) -> str:
        return export_format_by_key(export_format).encoder_label

    def probe_capabilities(self) -> FfmpegCapabilities:
        if self._capabilities is not None:
            return self._capabilities
        if not binary_path_available(self._binary_path):
            self._capabilities = FfmpegCapabilities()
            return self._capabilities
        try:
            encoders = subprocess.run(
                [self._binary_path, "-hide_banner", "-encoders"],
                shell=False,
                check=False,
                capture_output=True,
                **_hidden_subprocess_kwargs(),
            )
            hwaccels = subprocess.run(
                [self._binary_path, "-hide_banner", "-hwaccels"],
                shell=False,
                check=False,
                capture_output=True,
                **_hidden_subprocess_kwargs(),
            )
        except OSError:
            self._capabilities = FfmpegCapabilities()
            return self._capabilities

        encoder_text = encoders.stdout.decode("utf-8", errors="replace").lower()
        hwaccel_text = hwaccels.stdout.decode("utf-8", errors="replace").lower()
        self._capabilities = FfmpegCapabilities(
            prores_vulkan_available=(
                encoders.returncode == 0
                and hwaccels.returncode == 0
                and "prores_ks_vulkan" in encoder_text
                and "vulkan" in hwaccel_text
            )
        )
        return self._capabilities

    def run(
        self,
        command: list[str],
        log_path: Path,
        *,
        frame_stream,
        cancel_event: Event | None = None,
    ) -> None:
        self.ensure_available()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8") as log_handle:
            process = subprocess.Popen(
                command,
                shell=False,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=log_handle,
                **_hidden_subprocess_kwargs(),
            )
            try:
                assert process.stdin is not None
                pipe_write_times_ms: list[float] = []
                for frame_bytes in frame_stream:
                    if cancel_event is not None and cancel_event.is_set():
                        self._cancel_process(process=process, log_path=log_path, log_handle=log_handle)
                    write_started = perf_counter()
                    process.stdin.write(frame_bytes)
                    pipe_write_times_ms.append((perf_counter() - write_started) * 1000.0)
                if pipe_write_times_ms:
                    log_handle.write("\n[perf] pipe_write_summary\n")
                    log_handle.write(
                        "[perf] pipe_write_ms "
                        f"avg={_mean(pipe_write_times_ms):.3f} "
                        f"p95={_p95(pipe_write_times_ms):.3f} "
                        f"max={max(pipe_write_times_ms):.3f} "
                        f"frame_count={len(pipe_write_times_ms)}\n"
                    )
                process.stdin.close()
                while process.poll() is None:
                    if cancel_event is not None and cancel_event.is_set():
                        self._cancel_process(process=process, log_path=log_path, log_handle=log_handle)
                    sleep(0.05)
            except BrokenPipeError:
                if process.stdin is not None and not process.stdin.closed:
                    process.stdin.close()
                returncode = process.wait()
                log_handle.flush()
                stderr_text = self._read_log_text(log_path)
                raise subprocess.CalledProcessError(
                    returncode,
                    command,
                    "",
                    stderr_text,
                )

        stderr_text = self._read_log_text(log_path)
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command, "", stderr_text)
        if not stderr_text:
            log_path.write_text("ffmpeg completed", encoding="utf-8")

    def _cancel_process(
        self,
        *,
        process: subprocess.Popen,
        log_path: Path,
        log_handle,
    ) -> None:
        if process.stdin is not None and not process.stdin.closed:
            process.stdin.close()
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        log_handle.flush()
        log_text = self._read_log_text(log_path)
        log_text = "\n".join(part for part in [log_text, "ffmpeg cancelled"] if part)
        log_path.write_text(log_text, encoding="utf-8")
        raise ExportCancelledError("Export cancelled during MOV encoding.")

    @staticmethod
    def _read_log_text(log_path: Path) -> str:
        if not log_path.exists():
            return ""
        return log_path.read_text(encoding="utf-8", errors="replace").strip()


def _hidden_subprocess_kwargs() -> dict[str, object]:
    if os.name != "nt":
        return {}
    startupinfo_cls = getattr(subprocess, "STARTUPINFO", None)
    startupinfo = startupinfo_cls() if startupinfo_cls is not None else type("StartupInfo", (), {})()
    startupinfo.dwFlags = getattr(startupinfo, "dwFlags", 0) | getattr(
        subprocess,
        "STARTF_USESHOWWINDOW",
        1,
    )
    startupinfo.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
    return {
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
        "startupinfo": startupinfo,
    }


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * 0.95)))
    return ordered[index]
