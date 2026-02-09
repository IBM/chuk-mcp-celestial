"""Tests for base provider abstract class."""

import pytest

from chuk_mcp_celestial.providers.base import CelestialProvider


class ConcreteProvider(CelestialProvider):
    """Concrete implementation for testing abstract base."""

    async def get_moon_phases(self, date: str, num_phases: int = 12):
        """Test implementation."""
        pass

    async def get_sun_moon_data(
        self,
        date: str,
        latitude: float,
        longitude: float,
        timezone: float | None = None,
        dst: bool | None = None,
        label: str | None = None,
    ):
        """Test implementation."""
        pass

    async def get_solar_eclipse_by_date(
        self,
        date: str,
        latitude: float,
        longitude: float,
        height: int = 0,
    ):
        """Test implementation."""
        pass

    async def get_solar_eclipses_by_year(self, year: int):
        """Test implementation."""
        pass

    async def get_earth_seasons(
        self,
        year: int,
        timezone: float | None = None,
        dst: bool | None = None,
    ):
        """Test implementation."""
        pass

    async def get_planet_position(
        self,
        planet: str,
        date: str,
        time: str,
        latitude: float,
        longitude: float,
        timezone: float | None = None,
    ):
        """Test implementation."""
        pass

    async def get_planet_events(
        self,
        planet: str,
        date: str,
        latitude: float,
        longitude: float,
        timezone: float | None = None,
        dst: bool | None = None,
    ):
        """Test implementation."""
        pass


class TestCelestialProvider:
    """Test abstract base provider."""

    def test_cannot_instantiate_abstract(self):
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            CelestialProvider()  # type: ignore

    @pytest.mark.asyncio
    async def test_concrete_implementation(self):
        """Test that concrete implementation can be instantiated."""
        provider = ConcreteProvider()
        assert isinstance(provider, CelestialProvider)

        # Test all methods can be called
        await provider.get_moon_phases("2024-01-01")
        await provider.get_sun_moon_data("2024-01-01", 40.7, -74.0)
        await provider.get_solar_eclipse_by_date("2024-04-08", 40.7, -74.0)
        await provider.get_solar_eclipses_by_year(2024)
        await provider.get_earth_seasons(2024)
        await provider.get_planet_position("Mars", "2025-01-15", "22:00", 40.7, -74.0)
        await provider.get_planet_events("Jupiter", "2025-06-15", 40.7, -74.0)


class TestAbstractMethodBodies:
    """Test that abstract method bodies can be invoked via super()."""

    @pytest.mark.asyncio
    async def test_abstract_get_moon_phases(self):
        """Cover the pass in get_moon_phases."""
        p = ConcreteProvider()
        result = await CelestialProvider.get_moon_phases(p, "2024-01-01")
        assert result is None

    @pytest.mark.asyncio
    async def test_abstract_get_sun_moon_data(self):
        """Cover the pass in get_sun_moon_data."""
        p = ConcreteProvider()
        result = await CelestialProvider.get_sun_moon_data(p, "2024-01-01", 40.7, -74.0)
        assert result is None

    @pytest.mark.asyncio
    async def test_abstract_get_solar_eclipse_by_date(self):
        """Cover the pass in get_solar_eclipse_by_date."""
        p = ConcreteProvider()
        result = await CelestialProvider.get_solar_eclipse_by_date(p, "2024-04-08", 40.7, -74.0)
        assert result is None

    @pytest.mark.asyncio
    async def test_abstract_get_solar_eclipses_by_year(self):
        """Cover the pass in get_solar_eclipses_by_year."""
        p = ConcreteProvider()
        result = await CelestialProvider.get_solar_eclipses_by_year(p, 2024)
        assert result is None

    @pytest.mark.asyncio
    async def test_abstract_get_earth_seasons(self):
        """Cover the pass in get_earth_seasons."""
        p = ConcreteProvider()
        result = await CelestialProvider.get_earth_seasons(p, 2024)
        assert result is None

    @pytest.mark.asyncio
    async def test_abstract_get_planet_position(self):
        """Cover the pass in get_planet_position."""
        p = ConcreteProvider()
        result = await CelestialProvider.get_planet_position(
            p, "Mars", "2025-01-15", "22:00", 40.7, -74.0
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_abstract_get_planet_events(self):
        """Cover the pass in get_planet_events."""
        p = ConcreteProvider()
        result = await CelestialProvider.get_planet_events(p, "Mars", "2025-01-15", 40.7, -74.0)
        assert result is None


class TestIncompleteProvider:
    """Test that incomplete implementations cannot be instantiated."""

    def test_missing_planet_methods(self):
        """Test that a provider missing planet methods cannot be instantiated."""

        class IncompleteProvider(CelestialProvider):
            async def get_moon_phases(self, date, num_phases=12):
                pass

            async def get_sun_moon_data(
                self, date, latitude, longitude, timezone=None, dst=None, label=None
            ):
                pass

            async def get_solar_eclipse_by_date(self, date, latitude, longitude, height=0):
                pass

            async def get_solar_eclipses_by_year(self, year):
                pass

            async def get_earth_seasons(self, year, timezone=None, dst=None):
                pass

            # Missing get_planet_position and get_planet_events

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore
