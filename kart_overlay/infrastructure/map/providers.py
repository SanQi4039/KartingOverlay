from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass(frozen=True)
class EsriBasemapProvider:
    style_path: str = "ArcGIS/rest/services/World_Imagery/MapServer/tile"
    api_key: str | None = None

    def build_tile_url(self, zoom: int, x: int, y: int) -> str:
        base_url = f"https://server.arcgisonline.com/{self.style_path}/{zoom}/{y}/{x}"
        if not self.api_key:
            return base_url
        return f"{base_url}?{urlencode({'token': self.api_key})}"


def build_provider_registry(
    *,
    esri_api_key: str | None = None,
) -> dict[str, object]:
    return {
        "esri": EsriBasemapProvider(api_key=esri_api_key),
    }
