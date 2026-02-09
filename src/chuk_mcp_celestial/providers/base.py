"""Abstract base provider for celestial data calculations.

This module defines the interface that all providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..models import (
    MoonPhasesResponse,
    OneDayResponse,
    PlanetEventsResponse,
    PlanetPositionResponse,
    SeasonsResponse,
    SolarEclipseByDateResponse,
    SolarEclipseByYearResponse,
)


class CelestialProvider(ABC):
    """Abstract base class for celestial data providers.

    All provider implementations (Navy API, Skyfield, etc.) must implement
    these methods to provide a consistent interface.
    """

    @abstractmethod
    async def get_moon_phases(
        self,
        date: str,
        num_phases: int = 12,
    ) -> MoonPhasesResponse:
        """Get upcoming moon phases starting from a given date.

        Args:
            date: Start date in YYYY-MM-DD format
            num_phases: Number of phases to return (1-99)

        Returns:
            MoonPhasesResponse with list of phase data
        """
        pass

    @abstractmethod
    async def get_sun_moon_data(
        self,
        date: str,
        latitude: float,
        longitude: float,
        timezone: Optional[float] = None,
        dst: Optional[bool] = None,
        label: Optional[str] = None,
    ) -> OneDayResponse:
        """Get complete sun and moon data for one day at a specific location.

        Args:
            date: Date in YYYY-MM-DD format
            latitude: Latitude in decimal degrees (-90 to 90)
            longitude: Longitude in decimal degrees (-180 to 180)
            timezone: Timezone offset from UTC in hours
            dst: Whether to apply daylight saving time
            label: Optional user label

        Returns:
            OneDayResponse with sun/moon rise/set/transit times and moon phase
        """
        pass

    @abstractmethod
    async def get_solar_eclipse_by_date(
        self,
        date: str,
        latitude: float,
        longitude: float,
        height: int = 0,
    ) -> SolarEclipseByDateResponse:
        """Get local solar eclipse circumstances for a specific date and location.

        Args:
            date: Date of the eclipse in YYYY-MM-DD format
            latitude: Observer's latitude in decimal degrees
            longitude: Observer's longitude in decimal degrees
            height: Observer's height above mean sea level in meters

        Returns:
            SolarEclipseByDateResponse with eclipse details and local circumstances
        """
        pass

    @abstractmethod
    async def get_solar_eclipses_by_year(
        self,
        year: int,
    ) -> SolarEclipseByYearResponse:
        """Get a list of all solar eclipses occurring in a specific year.

        Args:
            year: Year to query (1800-2050)

        Returns:
            SolarEclipseByYearResponse with list of eclipse events
        """
        pass

    @abstractmethod
    async def get_earth_seasons(
        self,
        year: int,
        timezone: Optional[float] = None,
        dst: Optional[bool] = None,
    ) -> SeasonsResponse:
        """Get Earth's seasons and orbital events for a year.

        Args:
            year: Year to query (1700-2100)
            timezone: Timezone offset from UTC in hours
            dst: Whether to apply daylight saving time

        Returns:
            SeasonsResponse with equinoxes, solstices, perihelion, and aphelion
        """
        pass

    @abstractmethod
    async def get_planet_position(
        self,
        planet: str,
        date: str,
        time: str,
        latitude: float,
        longitude: float,
        timezone: Optional[float] = None,
    ) -> PlanetPositionResponse:
        """Get position and observational data for a planet.

        Args:
            planet: Planet name (Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto)
            date: Date in YYYY-MM-DD format
            time: Time in HH:MM format (UTC unless timezone specified)
            latitude: Observer latitude in decimal degrees (-90 to 90)
            longitude: Observer longitude in decimal degrees (-180 to 180)
            timezone: Timezone offset from UTC in hours

        Returns:
            PlanetPositionResponse with alt/az, RA/Dec, distance, magnitude, visibility
        """
        pass

    @abstractmethod
    async def get_planet_events(
        self,
        planet: str,
        date: str,
        latitude: float,
        longitude: float,
        timezone: Optional[float] = None,
        dst: Optional[bool] = None,
    ) -> PlanetEventsResponse:
        """Get rise, set, and transit times for a planet on a given day.

        Args:
            planet: Planet name (Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto)
            date: Date in YYYY-MM-DD format
            latitude: Observer latitude in decimal degrees (-90 to 90)
            longitude: Observer longitude in decimal degrees (-180 to 180)
            timezone: Timezone offset from UTC in hours
            dst: Whether to apply daylight saving time

        Returns:
            PlanetEventsResponse with rise/set/transit times
        """
        pass
