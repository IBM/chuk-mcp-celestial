"""Tests for celestial computation storage."""

import pytest

from chuk_mcp_celestial.core.celestial_storage import CelestialStorage


# ============================================================================
# Storage without artifact store (graceful degradation)
# ============================================================================


class TestStorageNoBackend:
    """Test storage when no artifact store is configured."""

    def test_available_false(self):
        storage = CelestialStorage()
        assert storage.available is False

    def test_storage_provider_none(self):
        storage = CelestialStorage()
        assert storage.storage_provider == "none"

    @pytest.mark.asyncio
    async def test_save_position_returns_none(self):
        storage = CelestialStorage()
        result = await storage.save_position(
            planet="Mars",
            date="2025-01-15",
            time="22:00",
            lat=47.6,
            lon=-122.3,
            data={"planet": "Mars", "altitude": 30.0},
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_save_events_returns_none(self):
        storage = CelestialStorage()
        result = await storage.save_events(
            planet="Mars",
            date="2025-01-15",
            lat=47.6,
            lon=-122.3,
            data={"planet": "Mars", "events": []},
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_save_still_caches_in_memory(self):
        """Even without artifact store, in-memory cache should work."""
        storage = CelestialStorage()
        await storage.save_position(
            planet="Mars",
            date="2025-01-15",
            time="22:00",
            lat=47.6,
            lon=-122.3,
            data={"planet": "Mars", "altitude": 30.0},
        )
        assert storage.stored_count() == 1

    @pytest.mark.asyncio
    async def test_load_from_cache(self):
        """Test loading from in-memory cache."""
        storage = CelestialStorage()
        test_data = {"planet": "Mars", "altitude": 30.0}
        await storage.save_position(
            planet="Mars",
            date="2025-01-15",
            time="22:00",
            lat=47.6,
            lon=-122.3,
            data=test_data,
        )

        key = "position|Mars|2025-01-15|22:00|47.6|-122.3"
        result = await storage.load(key)
        assert result is not None
        assert result["planet"] == "Mars"
        assert result["altitude"] == 30.0

    @pytest.mark.asyncio
    async def test_load_nonexistent_returns_none(self):
        storage = CelestialStorage()
        result = await storage.load("nonexistent|key")
        assert result is None


# ============================================================================
# Storage with mock artifact store
# ============================================================================


class MockArtifactStore:
    """Simple mock artifact store for testing."""

    def __init__(self):
        self._data: dict[str, bytes] = {}
        self._counter = 0
        self.storage_provider = "mock"

    async def store(self, data: bytes, mime: str, summary: str, filename: str, meta: dict) -> str:
        self._counter += 1
        artifact_id = f"mock-artifact-{self._counter}"
        self._data[artifact_id] = data
        return artifact_id

    async def retrieve(self, artifact_id: str) -> bytes:
        return self._data[artifact_id]


class TestStorageWithBackend:
    """Test storage with a mock artifact store."""

    def test_available_true(self):
        storage = CelestialStorage(artifact_store=MockArtifactStore())
        assert storage.available is True

    def test_storage_provider_name(self):
        storage = CelestialStorage(artifact_store=MockArtifactStore())
        assert storage.storage_provider == "mock"

    @pytest.mark.asyncio
    async def test_save_position_returns_artifact_id(self):
        storage = CelestialStorage(artifact_store=MockArtifactStore())
        result = await storage.save_position(
            planet="Mars",
            date="2025-01-15",
            time="22:00",
            lat=47.6,
            lon=-122.3,
            data={"planet": "Mars", "altitude": 30.0},
        )
        assert result is not None
        assert result.startswith("mock-artifact-")

    @pytest.mark.asyncio
    async def test_save_events_returns_artifact_id(self):
        storage = CelestialStorage(artifact_store=MockArtifactStore())
        result = await storage.save_events(
            planet="Jupiter",
            date="2025-06-15",
            lat=51.5,
            lon=-0.1,
            data={"planet": "Jupiter", "events": [{"phen": "Rise", "time": "04:30"}]},
        )
        assert result is not None
        assert result.startswith("mock-artifact-")

    @pytest.mark.asyncio
    async def test_load_from_artifact_store(self):
        """Test loading from artifact store when not in cache."""
        mock_store = MockArtifactStore()
        storage = CelestialStorage(artifact_store=mock_store)

        test_data = {"planet": "Mars", "altitude": 30.0}
        await storage.save_position(
            planet="Mars",
            date="2025-01-15",
            time="22:00",
            lat=47.6,
            lon=-122.3,
            data=test_data,
        )

        # Clear the in-memory cache to force loading from store
        storage._cache.clear()

        key = "position|Mars|2025-01-15|22:00|47.6|-122.3"
        result = await storage.load(key)
        assert result is not None
        assert result["planet"] == "Mars"

    @pytest.mark.asyncio
    async def test_stored_count(self):
        storage = CelestialStorage(artifact_store=MockArtifactStore())
        assert storage.stored_count() == 0

        await storage.save_position(
            planet="Mars",
            date="2025-01-15",
            time="22:00",
            lat=47.6,
            lon=-122.3,
            data={"test": 1},
        )
        assert storage.stored_count() == 1

        await storage.save_events(
            planet="Jupiter",
            date="2025-06-15",
            lat=51.5,
            lon=-0.1,
            data={"test": 2},
        )
        assert storage.stored_count() == 2

    @pytest.mark.asyncio
    async def test_artifact_metadata_position(self):
        """Test that position storage passes correct metadata."""
        calls = []

        class TrackingStore:
            storage_provider = "tracking"

            async def store(self, **kwargs):
                calls.append(kwargs)
                return "track-1"

        storage = CelestialStorage(artifact_store=TrackingStore())
        await storage.save_position(
            planet="Venus",
            date="2025-03-01",
            time="18:00",
            lat=51.48,
            lon=0.0,
            data={"planet": "Venus"},
        )

        assert len(calls) == 1
        call = calls[0]
        assert call["mime"] == "application/json"
        assert "Venus" in call["summary"]
        assert call["meta"]["type"] == "planet_position"
        assert call["meta"]["planet"] == "Venus"
        assert call["meta"]["date"] == "2025-03-01"

    @pytest.mark.asyncio
    async def test_artifact_metadata_events(self):
        """Test that events storage passes correct metadata."""
        calls = []

        class TrackingStore:
            storage_provider = "tracking"

            async def store(self, **kwargs):
                calls.append(kwargs)
                return "track-1"

        storage = CelestialStorage(artifact_store=TrackingStore())
        await storage.save_events(
            planet="Saturn",
            date="2025-06-15",
            lat=47.6,
            lon=-122.3,
            data={"planet": "Saturn", "events": []},
        )

        assert len(calls) == 1
        call = calls[0]
        assert call["mime"] == "application/json"
        assert "Saturn" in call["summary"]
        assert call["meta"]["type"] == "planet_events"
        assert call["meta"]["planet"] == "Saturn"


# ============================================================================
# Error handling
# ============================================================================


class TestStorageErrorHandling:
    """Test storage graceful error handling."""

    @pytest.mark.asyncio
    async def test_store_error_returns_none(self):
        """Test that storage errors are caught and return None."""

        class FailingStore:
            storage_provider = "failing"

            async def store(self, **kwargs):
                raise RuntimeError("Store failed")

        storage = CelestialStorage(artifact_store=FailingStore())
        result = await storage.save_position(
            planet="Mars",
            date="2025-01-15",
            time="22:00",
            lat=47.6,
            lon=-122.3,
            data={"test": True},
        )
        # Should return None, not raise
        assert result is None
        # But in-memory cache should still work
        assert storage.stored_count() == 1

    @pytest.mark.asyncio
    async def test_retrieve_error_returns_none(self):
        """Test that retrieval errors are caught and return None."""

        class FailRetrieveStore:
            storage_provider = "fail-retrieve"

            async def store(self, **kwargs):
                return "artifact-1"

            async def retrieve(self, artifact_id):
                raise RuntimeError("Retrieve failed")

        storage = CelestialStorage(artifact_store=FailRetrieveStore())
        await storage.save_position(
            planet="Mars",
            date="2025-01-15",
            time="22:00",
            lat=47.6,
            lon=-122.3,
            data={"test": True},
        )

        # Clear cache to force retrieval
        storage._cache.clear()

        key = "position|Mars|2025-01-15|22:00|47.6|-122.3"
        result = await storage.load(key)
        assert result is None
