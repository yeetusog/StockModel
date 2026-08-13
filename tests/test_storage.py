# saved data is what we train on later
import json

import pytest

from app.models.snapshot import MarketSnapshot, PriceData
from app.services import storage


@pytest.fixture
def snap_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "SNAPSHOTS_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def snap():
    return MarketSnapshot(
        snapshot_id="AAPL_20260810_120000",
        ticker="AAPL",
        timestamp="2026-08-10T12:00:00+00:00",
        price=PriceData(current=313.33),
    )


@pytest.mark.unit
def test_save_writes_latest_and_archive(snap_dir, snap):
    storage.save_snapshot(snap)

    assert (snap_dir / "AAPL_latest.json").exists()
    assert (snap_dir / "AAPL_20260810_120000.json").exists()


@pytest.mark.unit
def test_archive_is_write_once(snap_dir, snap):
    """Re-signalling the same snapshot must not rewrite history."""
    storage.save_snapshot(snap)
    archive = snap_dir / "AAPL_20260810_120000.json"
    first = archive.read_text()

    snap.price = PriceData(current=999.99)
    storage.save_snapshot(snap)

    assert archive.read_text() == first


@pytest.mark.unit
def test_latest_is_overwritten(snap_dir, snap):
    storage.save_snapshot(snap)
    snap.price = PriceData(current=999.99)
    storage.save_snapshot(snap)

    latest = json.loads((snap_dir / "AAPL_latest.json").read_text())
    assert latest["price"]["current"] == 999.99


@pytest.mark.unit
def test_round_trip_preserves_data(snap_dir, snap):
    storage.save_snapshot(snap)
    loaded = storage.load_latest_snapshot("AAPL")

    assert loaded is not None
    assert loaded.ticker == "AAPL"
    assert loaded.price.current == 313.33


@pytest.mark.unit
def test_missing_snapshot_returns_none(snap_dir):
    assert storage.load_latest_snapshot("NOSUCH") is None


@pytest.mark.unit
def test_corrupt_snapshot_returns_none_instead_of_raising(snap_dir):
    (snap_dir / "AAPL_latest.json").write_text("{ not json")
    assert storage.load_latest_snapshot("AAPL") is None


@pytest.mark.unit
def test_no_temp_files_left_behind(snap_dir, snap):
    """Atomic write uses a .tmp file — it must not survive a successful save."""
    storage.save_snapshot(snap)
    assert list(snap_dir.glob("*.tmp")) == []


@pytest.mark.unit
def test_history_skips_corrupt_files(snap_dir, snap):
    storage.save_snapshot(snap)
    (snap_dir / "AAPL_20260810_999999.json").write_text("{ broken")

    history = storage.load_history("AAPL", limit=10)

    assert len(history) == 1
    assert history[0]["ticker"] == "AAPL"


@pytest.mark.unit
def test_history_excludes_the_latest_pointer(snap_dir, snap):
    """load_history globs archives only — *_latest.json would be a duplicate row."""
    storage.save_snapshot(snap)
    assert len(storage.load_history("AAPL", limit=10)) == 1
