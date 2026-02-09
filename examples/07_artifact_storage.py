#!/usr/bin/env python3
"""Example: Artifact Storage for Computation Results

Demonstrates how planet computation results are stored via chuk-artifacts
for retrieval, audit, and cross-server integration.

Requires: pip install "chuk-mcp-celestial[skyfield]"
"""

import asyncio
import os

# Use memory backend for both ephemeris and artifacts
os.environ.setdefault("SKYFIELD_STORAGE_BACKEND", "memory")
os.environ.setdefault("CHUK_ARTIFACTS_PROVIDER", "memory")

from chuk_mcp_celestial.core.celestial_storage import CelestialStorage


async def main():
    print("=" * 70)
    print("Artifact Storage Example")
    print("=" * 70)

    # 1. Storage without backend (graceful degradation)
    print("\n1. Storage Without Backend (Graceful Degradation)")
    print("-" * 70)
    storage = CelestialStorage()
    print(f"  Available: {storage.available}")
    print(f"  Provider:  {storage.storage_provider}")

    result = await storage.save_position(
        planet="Mars",
        date="2025-01-15",
        time="22:00",
        lat=47.6,
        lon=-122.3,
        data={"planet": "Mars", "altitude": 30.0, "azimuth": 260.5},
    )
    print(f"  save_position returned: {result} (None = no store, still cached)")
    print(f"  Cached items: {storage.stored_count()}")

    # Load from cache
    cached = await storage.load("position|Mars|2025-01-15|22:00|47.6|-122.3")
    print(f"  Loaded from cache: {cached}")

    # 2. Storage with mock backend
    print("\n2. Storage With Mock Backend")
    print("-" * 70)

    class MockStore:
        """Simple in-memory artifact store for demo."""

        def __init__(self):
            self._data = {}
            self._counter = 0
            self.storage_provider = "mock-memory"

        async def store(self, data, mime, summary, filename, meta):
            self._counter += 1
            aid = f"artifact-{self._counter}"
            self._data[aid] = {"data": data, "meta": meta, "summary": summary}
            print(f"    Stored artifact: {aid}")
            print(f"    Summary: {summary}")
            print(f"    Filename: {filename}")
            print(f"    Metadata: {meta}")
            return aid

        async def retrieve(self, artifact_id):
            return self._data[artifact_id]["data"]

    mock = MockStore()
    storage = CelestialStorage(artifact_store=mock)
    print(f"  Available: {storage.available}")
    print(f"  Provider:  {storage.storage_provider}")

    # Save a position
    print("\n  Saving planet position...")
    artifact_id = await storage.save_position(
        planet="Jupiter",
        date="2025-06-15",
        time="21:00",
        lat=51.5,
        lon=-0.1,
        data={
            "planet": "Jupiter",
            "altitude": 42.3,
            "azimuth": 180.0,
            "magnitude": -2.7,
            "constellation": "Gem",
            "visibility": "visible",
        },
    )
    print(f"\n  Artifact ID: {artifact_id}")
    print(f"  Cached items: {storage.stored_count()}")

    # Save an events result
    print("\n  Saving planet events...")
    artifact_id = await storage.save_events(
        planet="Saturn",
        date="2025-06-15",
        lat=47.6,
        lon=-122.3,
        data={
            "planet": "Saturn",
            "events": [
                {"phen": "Rise", "time": "23:15"},
                {"phen": "Upper Transit", "time": "04:30"},
                {"phen": "Set", "time": "09:45"},
            ],
        },
    )
    print(f"\n  Artifact ID: {artifact_id}")
    print(f"  Cached items: {storage.stored_count()}")

    # 3. Error handling
    print("\n3. Error Handling (Graceful Degradation)")
    print("-" * 70)

    class FailingStore:
        storage_provider = "failing"

        async def store(self, **kwargs):
            raise RuntimeError("Simulated store failure!")

    storage = CelestialStorage(artifact_store=FailingStore())
    result = await storage.save_position(
        planet="Mars",
        date="2025-01-15",
        time="22:00",
        lat=47.6,
        lon=-122.3,
        data={"planet": "Mars"},
    )
    print(f"  Store failed gracefully, returned: {result}")
    print(f"  Data still cached in memory: {storage.stored_count()} items")

    print("\n" + "=" * 70)
    print("Artifact Storage Example Complete!")
    print("=" * 70)
    print("\nKey points:")
    print("  - Storage is optional; all operations are no-ops without a store")
    print("  - In-memory cache provides fast lookups within the process")
    print("  - Errors are caught and logged; tools never fail due to storage issues")
    print("  - Configure via CHUK_ARTIFACTS_PROVIDER env var (memory, s3, filesystem)")


if __name__ == "__main__":
    asyncio.run(main())
