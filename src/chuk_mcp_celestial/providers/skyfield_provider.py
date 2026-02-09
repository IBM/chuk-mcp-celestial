"""Skyfield-based celestial calculations provider.

This provider uses the Skyfield library for local astronomical calculations.
Requires skyfield package and ephemeris data files.

Storage backends:
- local: Traditional local filesystem storage
- s3: Cloud storage using chuk-virtual-fs with S3 backend
- memory: In-memory storage for testing
"""

import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from chuk_virtual_fs import AsyncVirtualFileSystem

from ..config import SkyfieldConfig
from ..constants import (
    PLANET_ABSOLUTE_MAGNITUDE,
    PLANET_MIN_ELONGATION,
    PLANET_SKYFIELD_NAMES,
)
from ..models import (
    GeoJSONPoint,
    MoonPhase,
    MoonPhaseData,
    MoonPhasesResponse,
    OneDayResponse,
    Planet,
    PlanetEventData,
    PlanetEventsData,
    PlanetEventsProperties,
    PlanetEventsResponse,
    PlanetPositionData,
    PlanetPositionProperties,
    PlanetPositionResponse,
    SeasonsResponse,
    SolarEclipseByDateResponse,
    SolarEclipseByYearResponse,
    VisibilityStatus,
)
from .base import CelestialProvider

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from skyfield import almanac
    from skyfield.api import Loader, wgs84
    from skyfield.magnitudelib import planetary_magnitude

    SKYFIELD_AVAILABLE = True
except ImportError:
    SKYFIELD_AVAILABLE = False
    logger.warning("Skyfield library not available. Install with: pip install skyfield")


class SkyfieldProvider(CelestialProvider):
    """Provider implementation using Skyfield for local calculations.

    This provider performs astronomical calculations locally using the
    Skyfield library and JPL ephemeris data.

    Advantages:
    - Offline calculations (after ephemeris download)
    - Faster (no network latency)
    - Research-grade accuracy

    Limitations:
    - Solar eclipse local circumstances not natively supported (workaround available)
    - Requires ~10-50 MB ephemeris data download
    """

    def __init__(
        self,
        ephemeris_file: str | None = None,
        storage_backend: str | None = None,
        auto_download: bool | None = None,
    ):
        """Initialize Skyfield provider.

        Args:
            ephemeris_file: Ephemeris file to use (default: from config)
            storage_backend: Storage backend - 'local', 's3', or 'memory' (default: from config)
            auto_download: Auto-download ephemeris if not present (default: True)

        Raises:
            ImportError: If skyfield is not installed
        """
        if not SKYFIELD_AVAILABLE:
            raise ImportError(
                "Skyfield library is required for this provider. Install with: pip install skyfield"
            )

        self.ephemeris_file = ephemeris_file or SkyfieldConfig.EPHEMERIS_FILE
        self.storage_backend = storage_backend or SkyfieldConfig.STORAGE_BACKEND
        self.auto_download = (
            auto_download if auto_download is not None else SkyfieldConfig.AUTO_DOWNLOAD
        )

        # Virtual filesystem for ephemeris storage
        self._vfs: Optional[AsyncVirtualFileSystem] = None
        self._vfs_initialized = False

        # Local cache directory for Skyfield to read from
        # Skyfield needs actual files on disk, so we cache from VFS
        self.cache_dir = Path(tempfile.gettempdir()) / "chuk-celestial-cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Skyfield loader with cache directory
        self.loader = Loader(str(self.cache_dir), verbose=False)

        # Load timescale (small file, auto-downloaded by Skyfield)
        self.ts = self.loader.timescale()

        # Load ephemeris (lazy loaded on first use)
        self._eph = None

        logger.debug(
            f"Skyfield provider initialized: backend={self.storage_backend}, "
            f"ephemeris={self.ephemeris_file}, cache={self.cache_dir}"
        )

    async def _initialize_vfs(self):
        """Initialize virtual filesystem if not already done."""
        if self._vfs_initialized:
            return

        if self.storage_backend == "local":
            # Local storage - use traditional directory
            data_dir = Path(SkyfieldConfig.DATA_DIR).expanduser()
            self._vfs = AsyncVirtualFileSystem(provider="filesystem", root_path=str(data_dir))
        elif self.storage_backend == "s3":
            # S3 storage with chuk-virtual-fs
            self._vfs = AsyncVirtualFileSystem(
                provider="s3",
                bucket_name=SkyfieldConfig.S3_BUCKET,
                prefix=SkyfieldConfig.S3_PREFIX,
                region_name=SkyfieldConfig.S3_REGION,
            )
        elif self.storage_backend == "memory":
            # In-memory storage (for testing)
            self._vfs = AsyncVirtualFileSystem(provider="memory")
        else:
            raise ValueError(
                f"Unknown storage backend: {self.storage_backend}. "
                "Must be 'local', 's3', or 'memory'"
            )

        await self._vfs.initialize()
        self._vfs_initialized = True
        logger.debug(f"Initialized VFS with {self.storage_backend} backend")

    async def _ensure_ephemeris_cached(self):
        """Ensure ephemeris file is available in local cache.

        Downloads from VFS storage if needed.
        """
        await self._initialize_vfs()

        cache_path = self.cache_dir / self.ephemeris_file
        vfs_path = f"/{self.ephemeris_file}"

        # Check if already in cache
        if cache_path.exists():
            logger.debug(f"Ephemeris {self.ephemeris_file} found in cache")
            return

        # Try to download from VFS storage
        if await self._vfs.exists(vfs_path):
            logger.info(
                f"Downloading ephemeris {self.ephemeris_file} from {self.storage_backend} to cache"
            )
            content = await self._vfs.read_file(vfs_path)
            cache_path.write_bytes(content)
            logger.info(f"Cached ephemeris: {cache_path}")
        elif self.auto_download:
            # Let Skyfield download it, then upload to VFS
            logger.info(f"Ephemeris not found, letting Skyfield download {self.ephemeris_file}")
            # Skyfield will download to cache_dir via loader
            # After loading, we'll upload to VFS storage
        else:
            raise FileNotFoundError(
                f"Ephemeris file {self.ephemeris_file} not found in {self.storage_backend} "
                f"and auto_download is disabled"
            )

    @property
    def eph(self):
        """Lazy-load ephemeris data."""
        if self._eph is None:
            try:
                # Note: This is sync, but loading happens in async context
                # The actual caching is done in async methods before this is called
                self._eph = self.loader(self.ephemeris_file)
                logger.info(f"Loaded ephemeris: {self.ephemeris_file}")
            except Exception as e:
                logger.error(f"Failed to load ephemeris {self.ephemeris_file}: {e}")
                raise

        return self._eph

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
        # Ensure ephemeris is available in cache
        await self._ensure_ephemeris_cached()

        # Parse date
        year, month, day = map(int, date.split("-"))

        # Create time range
        t0 = self.ts.utc(year, month, day)

        # Estimate end time (num_phases * 7.4 days average per phase)
        # A lunar cycle is ~29.5 days, so 4 phases = 7.4 days per phase
        days = int(num_phases * 7.4) + 2  # Add buffer

        # Calculate end date
        start_dt = datetime(year, month, day)
        end_dt = start_dt + timedelta(days=days)
        t1 = self.ts.utc(end_dt.year, end_dt.month, end_dt.day)

        # Find phase events using Skyfield
        t, phase_codes = almanac.find_discrete(t0, t1, almanac.moon_phases(self.eph))

        # Convert to our Pydantic models
        phases = []
        for time_obj, code in zip(t[:num_phases], phase_codes[:num_phases]):
            utc_time = time_obj.utc_datetime()

            # Map Skyfield phase codes (0-3) to our enum
            phase_map = {
                0: MoonPhase.NEW_MOON,
                1: MoonPhase.FIRST_QUARTER,
                2: MoonPhase.FULL_MOON,
                3: MoonPhase.LAST_QUARTER,
            }

            phases.append(
                MoonPhaseData(
                    phase=phase_map[code],
                    year=utc_time.year,
                    month=utc_time.month,
                    day=utc_time.day,
                    time=f"{utc_time.hour:02d}:{utc_time.minute:02d}",
                )
            )

        return MoonPhasesResponse(
            apiversion="Skyfield 1.x",
            year=year,
            month=month,
            day=day,
            numphases=len(phases),
            phasedata=phases,
        )

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

        Note: This is a placeholder implementation. Full implementation requires
        converting Skyfield results to Navy API GeoJSON format.

        Args:
            date: Date in YYYY-MM-DD format
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            timezone: Timezone offset from UTC in hours
            dst: Whether to apply daylight saving time
            label: Optional user label

        Returns:
            OneDayResponse with sun/moon rise/set/transit times

        Raises:
            NotImplementedError: This method is not yet fully implemented
        """
        raise NotImplementedError(
            "Sun/Moon rise/set calculations with Skyfield are coming soon. "
            "Use Navy API provider for this functionality."
        )

    async def get_solar_eclipse_by_date(
        self,
        date: str,
        latitude: float,
        longitude: float,
        height: int = 0,
    ) -> SolarEclipseByDateResponse:
        """Get local solar eclipse circumstances for a specific date and location.

        Note: Skyfield does not natively support solar eclipse local circumstances.
        A workaround using angular separation is possible but not yet implemented.

        Args:
            date: Date of the eclipse in YYYY-MM-DD format
            latitude: Observer's latitude in decimal degrees
            longitude: Observer's longitude in decimal degrees
            height: Observer's height above mean sea level in meters

        Returns:
            SolarEclipseByDateResponse with eclipse details

        Raises:
            NotImplementedError: This method is not yet implemented
        """
        raise NotImplementedError(
            "Solar eclipse calculations are not supported in Skyfield provider. "
            "Use Navy API provider for this functionality."
        )

    async def get_solar_eclipses_by_year(
        self,
        year: int,
    ) -> SolarEclipseByYearResponse:
        """Get a list of all solar eclipses occurring in a specific year.

        Note: Skyfield does not have built-in solar eclipse search.

        Args:
            year: Year to query

        Returns:
            SolarEclipseByYearResponse with list of eclipse events

        Raises:
            NotImplementedError: This method is not yet implemented
        """
        raise NotImplementedError(
            "Solar eclipse search is not supported in Skyfield provider. "
            "Use Navy API provider for this functionality."
        )

    async def get_earth_seasons(
        self,
        year: int,
        timezone: Optional[float] = None,
        dst: Optional[bool] = None,
    ) -> SeasonsResponse:
        """Get Earth's seasons and orbital events for a year.

        Uses Skyfield's almanac.seasons() to find equinoxes and solstices.
        Note: Perihelion and aphelion are not yet implemented.

        Args:
            year: Year to query
            timezone: Timezone offset from UTC in hours
            dst: Whether to apply daylight saving time

        Returns:
            SeasonsResponse with equinoxes and solstices
        """
        # Ensure ephemeris is available in cache
        await self._ensure_ephemeris_cached()

        from ..models import SeasonEvent, SeasonPhenomenon

        # Create time range for the year
        t0 = self.ts.utc(year, 1, 1)
        t1 = self.ts.utc(year + 1, 1, 1)

        # Find season events using Skyfield
        t, season_codes = almanac.find_discrete(t0, t1, almanac.seasons(self.eph))

        # Map Skyfield season codes to our enums
        # Skyfield: 0=March Equinox, 1=June Solstice, 2=September Equinox, 3=December Solstice
        season_map = {
            0: ("March Equinox", SeasonPhenomenon.EQUINOX),
            1: ("June Solstice", SeasonPhenomenon.SOLSTICE),
            2: ("September Equinox", SeasonPhenomenon.EQUINOX),
            3: ("December Solstice", SeasonPhenomenon.SOLSTICE),
        }

        # Convert to our Pydantic models
        season_events = []
        for time_obj, code in zip(t, season_codes):
            # Apply timezone offset if specified
            if timezone is not None:
                # Convert to UTC datetime, then adjust for timezone
                utc_time = time_obj.utc_datetime()
                offset_hours = timezone
                if dst:
                    offset_hours += 1  # Add DST hour
                adjusted_time = utc_time + timedelta(hours=offset_hours)
            else:
                adjusted_time = time_obj.utc_datetime()

            phenom_name, phenom_type = season_map[code]

            season_events.append(
                SeasonEvent(
                    phenom=phenom_type,  # Use the enum directly
                    year=adjusted_time.year,
                    month=adjusted_time.month,
                    day=adjusted_time.day,
                    time=f"{adjusted_time.hour:02d}:{adjusted_time.minute:02d}",
                )
            )

        # Note: Perihelion and Aphelion are not calculated by Skyfield's almanac
        # They would require orbital mechanics calculations

        return SeasonsResponse(
            apiversion="Skyfield 1.x",
            year=year,
            tz=timezone if timezone is not None else 0.0,
            dst=dst if dst is not None else False,
            data=season_events,
        )

    # ====================================================================
    # Planet helpers
    # ====================================================================

    def _resolve_planet(self, planet_name: str):
        """Resolve a planet name to a Skyfield ephemeris object.

        Args:
            planet_name: Planet name (e.g., "Mars")

        Returns:
            Skyfield ephemeris body

        Raises:
            ValueError: If planet name is not recognised
        """
        skyfield_name = PLANET_SKYFIELD_NAMES.get(planet_name)
        if skyfield_name is None:
            valid = ", ".join(PLANET_SKYFIELD_NAMES.keys())
            raise ValueError(f"Unknown planet: {planet_name}. Valid planets: {valid}")
        return self.eph[skyfield_name]

    def _compute_visibility(
        self, altitude: float, elongation: float, planet_name: str
    ) -> VisibilityStatus:
        """Determine planet visibility from altitude and elongation."""
        if altitude < 0:
            return VisibilityStatus.BELOW_HORIZON
        min_elong = PLANET_MIN_ELONGATION.get(planet_name, 10.0)
        if elongation < min_elong:
            return VisibilityStatus.LOST_IN_SUNLIGHT
        return VisibilityStatus.VISIBLE

    def _estimate_magnitude(
        self, planet_name: str, distance_au: float, sun_distance_au: float, phase_angle_deg: float
    ) -> float:
        """Estimate apparent visual magnitude for a planet.

        Uses Skyfield's planetary_magnitude when available, falls back to
        a simple distance-based estimate.
        """
        try:
            # planetary_magnitude expects specific planet identifiers
            # We need the astrometric position — caller should use the
            # dedicated Skyfield function instead.  This is the fallback.
            pass
        except Exception:
            pass

        # Simple fallback: H + 5*log10(r * delta)
        H = PLANET_ABSOLUTE_MAGNITUDE.get(planet_name, 0.0)
        if distance_au > 0 and sun_distance_au > 0:
            import math

            mag = H + 5.0 * math.log10(distance_au * sun_distance_au)
            return round(mag, 1)
        return H

    # ====================================================================
    # Planet Position
    # ====================================================================

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

        Uses Skyfield to compute topocentric position (alt/az), equatorial
        coordinates (RA/Dec), distance, elongation, and visibility.
        """
        await self._ensure_ephemeris_cached()

        # Validate planet
        try:
            planet_enum = Planet(planet)
        except ValueError:
            valid = ", ".join(p.value for p in Planet)
            raise ValueError(f"Unknown planet: {planet}. Valid: {valid}")

        planet_body = self._resolve_planet(planet)

        # Parse date and time
        year, month, day = map(int, date.split("-"))
        hour, minute = map(int, time.split(":"))

        # Apply timezone: convert local time to UTC for computation
        utc_hour = hour
        utc_minute = minute
        if timezone is not None:
            from datetime import datetime as dt, timedelta as td

            local = dt(year, month, day, hour, minute)
            utc = local - td(hours=timezone)
            year, month, day = utc.year, utc.month, utc.day
            utc_hour, utc_minute = utc.hour, utc.minute

        t = self.ts.utc(year, month, day, utc_hour, utc_minute)

        # Build observer location
        earth = self.eph["earth"]
        observer = earth + wgs84.latlon(latitude, longitude)

        # Observe planet
        astrometric = observer.at(t).observe(planet_body)
        apparent = astrometric.apparent()

        # Alt/Az
        alt, az, dist = apparent.altaz()
        altitude_deg = round(alt.degrees, 2)
        azimuth_deg = round(az.degrees, 2)

        # Distance
        distance_au = round(dist.au, 6)
        distance_km = round(dist.km, 0)

        # RA/Dec (J2000)
        ra, dec, _ = apparent.radec()
        ra_hours = ra.hours
        ra_h = int(ra_hours)
        ra_m = int((ra_hours - ra_h) * 60)
        ra_s = round(((ra_hours - ra_h) * 60 - ra_m) * 60, 1)
        ra_str = f"{ra_h:02d}:{ra_m:02d}:{ra_s:04.1f}"

        dec_deg = dec.degrees
        dec_sign = "+" if dec_deg >= 0 else "-"
        dec_abs = abs(dec_deg)
        dec_d = int(dec_abs)
        dec_m = int((dec_abs - dec_d) * 60)
        dec_s = round(((dec_abs - dec_d) * 60 - dec_m) * 60, 1)
        dec_str = f"{dec_sign}{dec_d:02d}:{dec_m:02d}:{dec_s:04.1f}"

        # Constellation
        try:
            from skyfield.api import load_constellation_map

            constellation_at = load_constellation_map()
            position = apparent
            constellation = constellation_at(position)
        except Exception:
            constellation = "N/A"

        # Elongation (angular separation from sun)
        sun = self.eph["sun"]
        sun_apparent = observer.at(t).observe(sun).apparent()
        elongation_angle = sun_apparent.separation_from(apparent)
        elongation_deg = round(elongation_angle.degrees, 1)

        # Sun distance from planet (for magnitude calculation)
        sun_astrometric = self.eph["sun"].at(t)
        planet_helio = self.eph[PLANET_SKYFIELD_NAMES[planet]].at(t)

        # Illumination (phase angle based)
        # Phase angle: angle Sun-Planet-Observer
        import math

        phase_angle_deg = 180.0 - elongation_deg  # rough approximation
        # Better: use the actual geometry
        try:
            # dot product of planet->observer and planet->sun vectors
            obs_vec = -np.array(astrometric.position.au)  # observer from planet
            sun_from_planet = np.array(sun_astrometric.position.au) - np.array(
                planet_helio.position.au
            )
            cos_phase = np.dot(obs_vec, sun_from_planet) / (
                np.linalg.norm(obs_vec) * np.linalg.norm(sun_from_planet)
            )
            cos_phase = np.clip(cos_phase, -1.0, 1.0)
            phase_angle_deg = math.degrees(math.acos(cos_phase))
        except Exception:
            pass

        illumination = round((1 + math.cos(math.radians(phase_angle_deg))) / 2 * 100, 1)

        # Magnitude
        try:
            mag = round(float(planetary_magnitude(astrometric)), 1)
        except Exception:
            sun_dist = np.linalg.norm(
                np.array(planet_helio.position.au) - np.array(sun_astrometric.position.au)
            )
            mag = self._estimate_magnitude(planet, distance_au, sun_dist, phase_angle_deg)

        # Visibility
        visibility = self._compute_visibility(altitude_deg, elongation_deg, planet)

        # Build response
        position_data = PlanetPositionData(
            planet=planet_enum,
            date=date,
            time=time,
            altitude=altitude_deg,
            azimuth=azimuth_deg,
            distance_au=distance_au,
            distance_km=distance_km,
            illumination=illumination,
            magnitude=mag,
            constellation=constellation,
            right_ascension=ra_str,
            declination=dec_str,
            elongation=elongation_deg,
            visibility=visibility,
        )

        return PlanetPositionResponse(
            apiversion="Skyfield 1.x",
            type="Feature",
            geometry=GeoJSONPoint(
                type="Point",
                coordinates=[longitude, latitude],
            ),
            properties=PlanetPositionProperties(data=position_data),
            artifact_ref=None,
        )

    # ====================================================================
    # Planet Events (Rise / Set / Transit)
    # ====================================================================

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

        Uses Skyfield almanac functions to find rise/set/transit events.
        """
        await self._ensure_ephemeris_cached()

        # Validate planet
        try:
            planet_enum = Planet(planet)
        except ValueError:
            valid = ", ".join(p.value for p in Planet)
            raise ValueError(f"Unknown planet: {planet}. Valid: {valid}")

        planet_body = self._resolve_planet(planet)

        # Parse date
        year, month, day = map(int, date.split("-"))

        # Time range: full day in UTC
        t0 = self.ts.utc(year, month, day)
        t1 = self.ts.utc(year, month, day + 1)

        # Build observer
        earth = self.eph["earth"]
        location = wgs84.latlon(latitude, longitude)
        observer = earth + location

        # Find risings and settings
        events: list[PlanetEventData] = []

        # Risings
        try:
            t_rise, rise_flags = almanac.find_risings(observer, planet_body, t0, t1)
            for t_event in t_rise:
                utc_dt = t_event.utc_datetime()
                if timezone is not None:
                    offset = timezone + (1 if dst else 0)
                    utc_dt = utc_dt + timedelta(hours=offset)
                events.append(
                    PlanetEventData(
                        phen="Rise",
                        time=f"{utc_dt.hour:02d}:{utc_dt.minute:02d}",
                    )
                )
        except Exception as e:
            logger.debug(f"No risings found for {planet}: {e}")

        # Settings
        try:
            t_set, set_flags = almanac.find_settings(observer, planet_body, t0, t1)
            for t_event in t_set:
                utc_dt = t_event.utc_datetime()
                if timezone is not None:
                    offset = timezone + (1 if dst else 0)
                    utc_dt = utc_dt + timedelta(hours=offset)
                events.append(
                    PlanetEventData(
                        phen="Set",
                        time=f"{utc_dt.hour:02d}:{utc_dt.minute:02d}",
                    )
                )
        except Exception as e:
            logger.debug(f"No settings found for {planet}: {e}")

        # Transit (meridian crossing — highest point)
        try:
            t_transit, transit_flags = almanac.find_transits(observer, planet_body, t0, t1)
            for t_event in t_transit:
                utc_dt = t_event.utc_datetime()
                if timezone is not None:
                    offset = timezone + (1 if dst else 0)
                    utc_dt = utc_dt + timedelta(hours=offset)
                events.append(
                    PlanetEventData(
                        phen="Upper Transit",
                        time=f"{utc_dt.hour:02d}:{utc_dt.minute:02d}",
                    )
                )
        except Exception as e:
            logger.debug(f"No transits found for {planet}: {e}")

        # Sort events by time
        events.sort(key=lambda e: e.time)

        # Get constellation and magnitude at noon
        t_noon = self.ts.utc(year, month, day, 12)
        astrometric = observer.at(t_noon).observe(planet_body)
        apparent = astrometric.apparent()

        try:
            from skyfield.api import load_constellation_map

            constellation_at = load_constellation_map()
            constellation = constellation_at(apparent)
        except Exception:
            constellation = "N/A"

        try:
            mag = round(float(planetary_magnitude(astrometric)), 1)
        except Exception:
            mag = PLANET_ABSOLUTE_MAGNITUDE.get(planet, 0.0)

        events_data = PlanetEventsData(
            planet=planet_enum,
            date=date,
            events=events,
            constellation=constellation,
            magnitude=mag,
        )

        return PlanetEventsResponse(
            apiversion="Skyfield 1.x",
            type="Feature",
            geometry=GeoJSONPoint(
                type="Point",
                coordinates=[longitude, latitude],
            ),
            properties=PlanetEventsProperties(data=events_data),
            artifact_ref=None,
        )
