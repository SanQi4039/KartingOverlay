from dataclasses import dataclass, field


@dataclass(frozen=True)
class Point2D:
    x: float
    y: float


@dataclass(frozen=True)
class DisplayTransform:
    translate_x: float = 0.0
    translate_y: float = 0.0
    rotation_deg: float = 0.0
    scale: float = 1.0


@dataclass(frozen=True)
class TimingLine:
    name: str
    start: Point2D
    end: Point2D
    direction: str = "any"
    min_speed_kmh: float = 0.0
    cooldown_time_sec: float = 0.0
    cooldown_distance_m: float = 0.0


@dataclass(frozen=True)
class SectorLine(TimingLine):
    order: int = 0


@dataclass(frozen=True)
class TrackDefinition:
    start_finish: TimingLine
    sectors: list[SectorLine] = field(default_factory=list)
    display_transform: DisplayTransform = field(default_factory=DisplayTransform)
    background_image_path: str = ""
