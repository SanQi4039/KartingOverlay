from dataclasses import dataclass

from kart_overlay.domain.track.models import Point2D, TimingLine


@dataclass(frozen=True)
class LineCrossing:
    cross_time_sec: float
    ratio: float


class LineCrossingDetector:
    def detect(
        self,
        *,
        line: TimingLine,
        previous_point: Point2D,
        current_point: Point2D,
        previous_time_sec: float,
        current_time_sec: float,
    ) -> LineCrossing | None:
        side_previous = self._signed_side(line.start, line.end, previous_point)
        side_current = self._signed_side(line.start, line.end, current_point)

        if side_previous == 0.0 and side_current == 0.0:
            return None

        if side_previous * side_current > 0:
            return None

        if line.direction == "positive_to_negative" and not (side_previous > 0 and side_current <= 0):
            return None

        if line.direction == "negative_to_positive" and not (side_previous < 0 and side_current >= 0):
            return None

        segment_dx = current_point.x - previous_point.x
        segment_dy = current_point.y - previous_point.y
        line_dx = line.end.x - line.start.x
        line_dy = line.end.y - line.start.y

        denominator = (segment_dx * line_dy) - (segment_dy * line_dx)
        if denominator == 0:
            return None

        ratio = (
            ((line.start.x - previous_point.x) * line_dy)
            - ((line.start.y - previous_point.y) * line_dx)
        ) / denominator

        if ratio < 0 or ratio > 1:
            return None

        cross_time_sec = previous_time_sec + ratio * (current_time_sec - previous_time_sec)
        return LineCrossing(cross_time_sec=cross_time_sec, ratio=ratio)

    @staticmethod
    def _signed_side(start: Point2D, end: Point2D, point: Point2D) -> float:
        return ((point.x - start.x) * (end.y - start.y)) - ((point.y - start.y) * (end.x - start.x))
