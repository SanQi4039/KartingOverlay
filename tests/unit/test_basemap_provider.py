from kart_overlay.infrastructure.map.providers import EsriBasemapProvider


def test_esri_provider_builds_tile_url():
    provider = EsriBasemapProvider()

    url = provider.build_tile_url(12, 3456, 1678)

    assert "arcgisonline.com" in url
    assert "/12/1678/3456" in url
