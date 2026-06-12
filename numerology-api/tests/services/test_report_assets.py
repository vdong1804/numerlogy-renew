"""Tests for report_assets path helpers (ornament graceful-degradation)."""

from app.services.report_assets import ornament


class TestOrnament:
    def test_existing_asset_returns_relative_path(self):
        # Shipped in static/report-assets/ornaments/
        assert ornament("corner-flourish") == \
            "static/report-assets/ornaments/corner-flourish.svg"
        assert ornament("sacred-geometry-watermark") == \
            "static/report-assets/ornaments/sacred-geometry-watermark.svg"

    def test_missing_asset_returns_none(self):
        assert ornament("does-not-exist") is None
