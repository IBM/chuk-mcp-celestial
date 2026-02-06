"""Unit tests for Skyfield provider (without network calls or actual Skyfield library)."""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from chuk_mcp_celestial.models import MoonPhase, SeasonPhenomenon

# Check if Skyfield is available
try:
    from chuk_mcp_celestial.providers.skyfield_provider import SKYFIELD_AVAILABLE
except ImportError:
    SKYFIELD_AVAILABLE = False

# Skip all tests if Skyfield is not available
pytestmark = pytest.mark.skipif(not SKYFIELD_AVAILABLE, reason="Skyfield not installed")


class TestSkyfieldProviderUnit:
    """Unit tests for Skyfield provider with mocked dependencies."""

    def test_initialization_without_skyfield(self):
        """Test that initialization fails if Skyfield is not available."""
        with patch("chuk_mcp_celestial.providers.skyfield_provider.SKYFIELD_AVAILABLE", False):
            from chuk_mcp_celestial.providers.skyfield_provider import SkyfieldProvider

            with pytest.raises(ImportError, match="Skyfield library is required"):
                SkyfieldProvider()

    def test_initialization_defaults(self):
        """Test provider initialization with defaults."""
        with patch("chuk_mcp_celestial.providers.skyfield_provider.SKYFIELD_AVAILABLE", True):
            with patch("chuk_mcp_celestial.providers.skyfield_provider.Loader") as mock_loader:
                # Mock timescale
                mock_ts = MagicMock()
                mock_loader_instance = MagicMock()
                mock_loader_instance.timescale.return_value = mock_ts
                mock_loader.return_value = mock_loader_instance

                from chuk_mcp_celestial.providers.skyfield_provider import SkyfieldProvider

                provider = SkyfieldProvider(storage_backend="memory", auto_download=True)

                assert provider.ephemeris_file is not None
                assert provider.storage_backend == "memory"
                assert provider.auto_download is True
                assert provider._vfs is None
                assert provider._vfs_initialized is False
                assert provider.cache_dir.exists()
                assert "chuk-celestial-cache" in str(provider.cache_dir)

    def test_initialization_custom_config(self):
        """Test provider initialization with custom configuration."""
        with patch("chuk_mcp_celestial.providers.skyfield_provider.SKYFIELD_AVAILABLE", True):
            with patch("chuk_mcp_celestial.providers.skyfield_provider.Loader"):
                from chuk_mcp_celestial.providers.skyfield_provider import SkyfieldProvider

                provider = SkyfieldProvider(
                    ephemeris_file="de440s.bsp",
                    storage_backend="local",
                    auto_download=False,
                )

                assert provider.ephemeris_file == "de440s.bsp"
                assert provider.storage_backend == "local"
                assert provider.auto_download is False

    @pytest.mark.asyncio
    async def test_initialize_vfs_memory_backend(self):
        """Test VFS initialization with memory backend."""
        with patch("chuk_mcp_celestial.providers.skyfield_provider.SKYFIELD_AVAILABLE", True):
            with patch("chuk_mcp_celestial.providers.skyfield_provider.Loader"):
                from chuk_mcp_celestial.providers.skyfield_provider import SkyfieldProvider

                provider = SkyfieldProvider(storage_backend="memory")

                with patch(
                    "chuk_mcp_celestial.providers.skyfield_provider.AsyncVirtualFileSystem"
                ) as mock_vfs:
                    mock_vfs_instance = AsyncMock()
                    mock_vfs.return_value = mock_vfs_instance

                    await provider._initialize_vfs()

                    assert provider._vfs_initialized is True
                    assert provider._vfs == mock_vfs_instance
                    mock_vfs.assert_called_once_with(provider="memory")
                    mock_vfs_instance.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_vfs_invalid_backend(self):
        """Test that invalid backend raises ValueError."""
        with patch("chuk_mcp_celestial.providers.skyfield_provider.SKYFIELD_AVAILABLE", True):
            with patch("chuk_mcp_celestial.providers.skyfield_provider.Loader"):
                from chuk_mcp_celestial.providers.skyfield_provider import SkyfieldProvider

                provider = SkyfieldProvider(storage_backend="invalid_backend")

                with pytest.raises(ValueError, match="Unknown storage backend"):
                    await provider._initialize_vfs()

    @pytest.mark.asyncio
    async def test_get_sun_moon_data_not_implemented(self):
        """Test that get_sun_moon_data raises NotImplementedError."""
        with patch("chuk_mcp_celestial.providers.skyfield_provider.SKYFIELD_AVAILABLE", True):
            with patch("chuk_mcp_celestial.providers.skyfield_provider.Loader"):
                from chuk_mcp_celestial.providers.skyfield_provider import SkyfieldProvider

                provider = SkyfieldProvider(storage_backend="memory")

                with pytest.raises(NotImplementedError, match="Sun/Moon rise/set calculations"):
                    await provider.get_sun_moon_data(
                        date="2024-01-01", latitude=40.7, longitude=-74.0
                    )

    @pytest.mark.asyncio
    async def test_get_solar_eclipse_by_date_not_implemented(self):
        """Test that get_solar_eclipse_by_date raises NotImplementedError."""
        with patch("chuk_mcp_celestial.providers.skyfield_provider.SKYFIELD_AVAILABLE", True):
            with patch("chuk_mcp_celestial.providers.skyfield_provider.Loader"):
                from chuk_mcp_celestial.providers.skyfield_provider import SkyfieldProvider

                provider = SkyfieldProvider(storage_backend="memory")

                with pytest.raises(
                    NotImplementedError, match="Solar eclipse calculations are not supported"
                ):
                    await provider.get_solar_eclipse_by_date(
                        date="2024-04-08", latitude=40.7, longitude=-74.0
                    )

    @pytest.mark.asyncio
    async def test_get_solar_eclipses_by_year_not_implemented(self):
        """Test that get_solar_eclipses_by_year raises NotImplementedError."""
        with patch("chuk_mcp_celestial.providers.skyfield_provider.SKYFIELD_AVAILABLE", True):
            with patch("chuk_mcp_celestial.providers.skyfield_provider.Loader"):
                from chuk_mcp_celestial.providers.skyfield_provider import SkyfieldProvider

                provider = SkyfieldProvider(storage_backend="memory")

                with pytest.raises(
                    NotImplementedError, match="Solar eclipse search is not supported"
                ):
                    await provider.get_solar_eclipses_by_year(year=2024)

    @pytest.mark.asyncio
    async def test_get_moon_phases_success(self):
        """Test successful moon phases calculation."""
        with patch("chuk_mcp_celestial.providers.skyfield_provider.SKYFIELD_AVAILABLE", True):
            with patch("chuk_mcp_celestial.providers.skyfield_provider.Loader") as mock_loader:
                with patch(
                    "chuk_mcp_celestial.providers.skyfield_provider.almanac"
                ) as mock_almanac:
                    # Setup mock loader and timescale
                    mock_ts = MagicMock()
                    mock_loader_instance = MagicMock()
                    mock_loader_instance.timescale.return_value = mock_ts
                    mock_loader.return_value = mock_loader_instance

                    from chuk_mcp_celestial.providers.skyfield_provider import SkyfieldProvider

                    provider = SkyfieldProvider(storage_backend="memory")

                    # Mock VFS
                    with patch(
                        "chuk_mcp_celestial.providers.skyfield_provider.AsyncVirtualFileSystem"
                    ) as mock_vfs:
                        mock_vfs_instance = AsyncMock()
                        mock_vfs.return_value = mock_vfs_instance

                        with patch.object(Path, "exists", return_value=True):
                            # Mock Skyfield time objects
                            mock_time_1 = MagicMock()
                            mock_time_1.utc_datetime.return_value = datetime(2024, 1, 11, 11, 57)
                            mock_time_2 = MagicMock()
                            mock_time_2.utc_datetime.return_value = datetime(2024, 1, 18, 3, 52)

                            # Mock find_discrete to return moon phases
                            mock_almanac.find_discrete.return_value = (
                                [mock_time_1, mock_time_2],
                                [0, 1],  # New, First Quarter
                            )
                            mock_almanac.moon_phases.return_value = MagicMock()

                            # Mock ephemeris
                            mock_eph = MagicMock()
                            with patch.object(
                                type(provider), "eph", new_callable=PropertyMock
                            ) as mock_eph_prop:
                                mock_eph_prop.return_value = mock_eph

                                result = await provider.get_moon_phases(
                                    date="2024-1-1", num_phases=2
                                )

                                assert result.year == 2024
                                assert result.month == 1
                                assert result.day == 1
                                assert result.numphases == 2
                                assert len(result.phasedata) == 2
                                assert result.phasedata[0].phase == MoonPhase.NEW_MOON
                                assert result.phasedata[1].phase == MoonPhase.FIRST_QUARTER

    @pytest.mark.asyncio
    async def test_get_earth_seasons_success(self):
        """Test successful earth seasons calculation."""
        with patch("chuk_mcp_celestial.providers.skyfield_provider.SKYFIELD_AVAILABLE", True):
            with patch("chuk_mcp_celestial.providers.skyfield_provider.Loader") as mock_loader:
                with patch(
                    "chuk_mcp_celestial.providers.skyfield_provider.almanac"
                ) as mock_almanac:
                    # Setup mock loader and timescale
                    mock_ts = MagicMock()
                    mock_loader_instance = MagicMock()
                    mock_loader_instance.timescale.return_value = mock_ts
                    mock_loader.return_value = mock_loader_instance

                    from chuk_mcp_celestial.providers.skyfield_provider import SkyfieldProvider

                    provider = SkyfieldProvider(storage_backend="memory")

                    # Mock VFS
                    with patch(
                        "chuk_mcp_celestial.providers.skyfield_provider.AsyncVirtualFileSystem"
                    ) as mock_vfs:
                        mock_vfs_instance = AsyncMock()
                        mock_vfs.return_value = mock_vfs_instance

                        with patch.object(Path, "exists", return_value=True):
                            # Mock Skyfield time objects
                            mock_time_1 = MagicMock()
                            mock_time_1.utc_datetime.return_value = datetime(2024, 3, 20, 3, 6)
                            mock_time_2 = MagicMock()
                            mock_time_2.utc_datetime.return_value = datetime(2024, 6, 20, 20, 50)

                            # Mock find_discrete to return seasons
                            mock_almanac.find_discrete.return_value = (
                                [mock_time_1, mock_time_2],
                                [0, 1],  # March Equinox, June Solstice
                            )
                            mock_almanac.seasons.return_value = MagicMock()

                            # Mock ephemeris
                            mock_eph = MagicMock()
                            with patch.object(
                                type(provider), "eph", new_callable=PropertyMock
                            ) as mock_eph_prop:
                                mock_eph_prop.return_value = mock_eph

                                result = await provider.get_earth_seasons(year=2024)

                                assert result.year == 2024
                                assert result.tz == 0.0
                                assert result.dst is False
                                assert len(result.data) == 2
                                assert result.data[0].phenom == SeasonPhenomenon.EQUINOX
                                assert result.data[1].phenom == SeasonPhenomenon.SOLSTICE
