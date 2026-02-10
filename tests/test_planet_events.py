"""Tests for planet events tool and Skyfield provider."""

import pytest

# Check if Skyfield is available
try:
    from chuk_mcp_celestial.providers.skyfield_provider import (
        SkyfieldProvider,
        SKYFIELD_AVAILABLE,
    )
except ImportError:
    SKYFIELD_AVAILABLE = False
    SkyfieldProvider = None  # type: ignore

from chuk_mcp_celestial.models import Planet

pytestmark = pytest.mark.skipif(not SKYFIELD_AVAILABLE, reason="Skyfield not installed")


@pytest.fixture
def skyfield_provider():
    """Create a Skyfield provider with memory backend."""
    return SkyfieldProvider(storage_backend="memory")


# ============================================================================
# Planet Events via Provider
# ============================================================================


@pytest.mark.asyncio
async def test_jupiter_events(skyfield_provider, seattle_coords):
    """Test getting Jupiter rise/set/transit events."""
    result = await skyfield_provider.get_planet_events(
        planet="Jupiter",
        date="2025-6-15",
        latitude=seattle_coords["latitude"],
        longitude=seattle_coords["longitude"],
    )

    assert result is not None
    assert result.type == "Feature"
    assert result.apiversion == "Skyfield 1.x"

    data = result.properties.data
    assert data.planet == Planet.JUPITER
    assert data.date == "2025-6-15"
    assert isinstance(data.events, list)
    assert isinstance(data.constellation, str)
    assert isinstance(data.magnitude, float)

    # Jupiter should normally have rise/set/transit events at mid-latitudes
    if data.events:
        for event in data.events:
            assert event.phen in ("Rise", "Set", "Upper Transit")
            assert ":" in event.time


@pytest.mark.asyncio
async def test_all_planets_events(skyfield_provider, seattle_coords):
    """Test events for each supported planet."""
    for planet in Planet:
        result = await skyfield_provider.get_planet_events(
            planet=planet.value,
            date="2025-6-15",
            latitude=seattle_coords["latitude"],
            longitude=seattle_coords["longitude"],
        )
        assert result is not None
        assert result.properties.data.planet == planet


@pytest.mark.asyncio
async def test_events_with_timezone(skyfield_provider, seattle_coords):
    """Test events with timezone offset."""
    result = await skyfield_provider.get_planet_events(
        planet="Mars",
        date="2025-6-15",
        latitude=seattle_coords["latitude"],
        longitude=seattle_coords["longitude"],
        timezone=-7,
    )

    assert result is not None
    data = result.properties.data
    assert data.planet == Planet.MARS


@pytest.mark.asyncio
async def test_events_with_dst(skyfield_provider, seattle_coords):
    """Test events with DST applied."""
    result = await skyfield_provider.get_planet_events(
        planet="Venus",
        date="2025-6-15",
        latitude=seattle_coords["latitude"],
        longitude=seattle_coords["longitude"],
        timezone=-8,
        dst=True,
    )

    assert result is not None
    data = result.properties.data
    assert data.planet == Planet.VENUS


@pytest.mark.asyncio
async def test_invalid_planet_events(skyfield_provider, seattle_coords):
    """Test that invalid planet name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown planet"):
        await skyfield_provider.get_planet_events(
            planet="InvalidPlanet",
            date="2025-1-15",
            latitude=seattle_coords["latitude"],
            longitude=seattle_coords["longitude"],
        )


@pytest.mark.asyncio
async def test_events_geojson_structure(skyfield_provider, greenwich_coords):
    """Test GeoJSON Feature output structure."""
    result = await skyfield_provider.get_planet_events(
        planet="Saturn",
        date="2025-3-1",
        latitude=greenwich_coords["latitude"],
        longitude=greenwich_coords["longitude"],
    )

    data = result.model_dump()
    assert data["type"] == "Feature"
    assert "geometry" in data
    assert data["geometry"]["type"] == "Point"
    assert len(data["geometry"]["coordinates"]) == 2
    assert "properties" in data
    assert "data" in data["properties"]

    events_data = data["properties"]["data"]
    assert "planet" in events_data
    assert "date" in events_data
    assert "events" in events_data
    assert "constellation" in events_data
    assert "magnitude" in events_data


@pytest.mark.asyncio
async def test_events_sorted_by_time(skyfield_provider, seattle_coords):
    """Test that events are sorted chronologically."""
    result = await skyfield_provider.get_planet_events(
        planet="Mars",
        date="2025-6-15",
        latitude=seattle_coords["latitude"],
        longitude=seattle_coords["longitude"],
    )

    events = result.properties.data.events
    if len(events) > 1:
        times = [e.time for e in events]
        assert times == sorted(times)


@pytest.mark.asyncio
async def test_events_southern_hemisphere(skyfield_provider, sydney_coords):
    """Test planet events for Southern Hemisphere location."""
    result = await skyfield_provider.get_planet_events(
        planet="Jupiter",
        date="2025-7-1",
        latitude=sydney_coords["latitude"],
        longitude=sydney_coords["longitude"],
    )

    assert result is not None
    assert result.geometry.coordinates[0] == pytest.approx(sydney_coords["longitude"], abs=0.1)
    assert result.geometry.coordinates[1] == pytest.approx(sydney_coords["latitude"], abs=0.1)
