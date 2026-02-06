"""Unit tests for Navy API provider (without network calls)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from chuk_mcp_celestial.providers.navy import (
    NavyAPIProvider,
    NavyAPIEndpoints,
)
from chuk_mcp_celestial.models import MoonPhase


class TestNavyAPIEndpoints:
    """Test Navy API endpoint URL construction."""

    def test_endpoint_construction(self):
        """Test that endpoints are constructed correctly."""
        base_url = "https://api.example.com"
        endpoints = NavyAPIEndpoints(base_url)

        assert endpoints.base == base_url
        assert endpoints.moon_phases == f"{base_url}/moon/phases/date"
        assert endpoints.rstt_oneday == f"{base_url}/rstt/oneday"
        assert endpoints.solar_eclipse_date == f"{base_url}/eclipses/solar/date"
        assert endpoints.solar_eclipse_year == f"{base_url}/eclipses/solar/year"
        assert endpoints.seasons == f"{base_url}/seasons"


class TestNavyAPIProvider:
    """Test Navy API provider methods."""

    @pytest.fixture
    def provider(self):
        """Create a Navy API provider instance."""
        return NavyAPIProvider()

    @pytest.fixture
    def custom_provider(self):
        """Create a Navy API provider with custom config."""
        return NavyAPIProvider(base_url="https://custom.api.com", timeout=60.0)

    def test_initialization_defaults(self, provider):
        """Test provider initialization with defaults."""
        assert provider.base_url is not None
        assert provider.timeout is not None
        assert isinstance(provider.endpoints, NavyAPIEndpoints)

    def test_initialization_custom(self, custom_provider):
        """Test provider initialization with custom values."""
        assert custom_provider.base_url == "https://custom.api.com"
        assert custom_provider.timeout == 60.0

    @pytest.mark.asyncio
    async def test_get_moon_phases_success(self, provider):
        """Test successful moon phases API call."""
        mock_response_data = {
            "apiversion": "3.1.0",
            "year": 2024,
            "month": 1,
            "day": 1,
            "numphases": 4,
            "phasedata": [
                {
                    "phase": "New Moon",
                    "year": 2024,
                    "month": 1,
                    "day": 11,
                    "time": "11:57",
                },
                {
                    "phase": "First Quarter",
                    "year": 2024,
                    "month": 1,
                    "day": 18,
                    "time": "03:52",
                },
                {
                    "phase": "Full Moon",
                    "year": 2024,
                    "month": 1,
                    "day": 25,
                    "time": "17:54",
                },
                {
                    "phase": "Last Quarter",
                    "year": 2024,
                    "month": 2,
                    "day": 2,
                    "time": "23:18",
                },
            ],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await provider.get_moon_phases(date="2024-1-1", num_phases=4)

            assert result.year == 2024
            assert result.numphases == 4
            assert len(result.phasedata) == 4
            assert result.phasedata[0].phase == MoonPhase.NEW_MOON

            # Verify API was called with correct params
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args.kwargs
            assert call_kwargs["params"]["date"] == "2024-1-1"
            assert call_kwargs["params"]["nump"] == 4

    @pytest.mark.asyncio
    async def test_get_moon_phases_invalid_num_phases_min(self, provider):
        """Test moon phases with num_phases below minimum."""
        with pytest.raises(ValueError, match="num_phases must be between"):
            await provider.get_moon_phases(date="2024-1-1", num_phases=0)

    @pytest.mark.asyncio
    async def test_get_moon_phases_invalid_num_phases_max(self, provider):
        """Test moon phases with num_phases above maximum."""
        with pytest.raises(ValueError, match="num_phases must be between"):
            await provider.get_moon_phases(date="2024-1-1", num_phases=100)

    @pytest.mark.asyncio
    async def test_get_sun_moon_data_success(self, provider):
        """Test successful sun/moon data API call."""
        mock_response_data = {
            "apiversion": "3.1.0",
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [-74.0, 40.7, 0],
            },
            "properties": {
                "data": {
                    "year": 2024,
                    "month": 1,
                    "day": 1,
                    "day_of_week": "Monday",
                    "tz": 0.0,
                    "isdst": False,
                    "closestphase": {
                        "phase": "Full Moon",
                        "year": 2024,
                        "month": 1,
                        "day": 25,
                        "time": "17:54",
                    },
                    "curphase": "Waxing Gibbous",
                    "fracillum": "92%",
                    "sundata": [],
                    "moondata": [],
                }
            },
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await provider.get_sun_moon_data(
                date="2024-1-1", latitude=40.7, longitude=-74.0
            )

            assert result.geometry.coordinates == [-74.0, 40.7, 0]

            # Verify API was called with correct params
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args.kwargs
            assert call_kwargs["params"]["date"] == "2024-1-1"
            assert call_kwargs["params"]["coords"] == "40.7,-74.0"

    @pytest.mark.asyncio
    async def test_get_sun_moon_data_with_timezone_and_dst(self, provider):
        """Test sun/moon data with timezone and DST parameters."""
        mock_response_data = {
            "apiversion": "3.1.0",
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-74.0, 40.7, 0]},
            "properties": {
                "data": {
                    "year": 2024,
                    "month": 1,
                    "day": 1,
                    "day_of_week": "Monday",
                    "tz": -5.0,
                    "isdst": True,
                    "closestphase": {
                        "phase": "Full Moon",
                        "year": 2024,
                        "month": 1,
                        "day": 25,
                        "time": "17:54",
                    },
                    "curphase": "Waxing Gibbous",
                    "fracillum": "92%",
                    "sundata": [],
                    "moondata": [],
                }
            },
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            await provider.get_sun_moon_data(
                date="2024-1-1",
                latitude=40.7,
                longitude=-74.0,
                timezone=-5.0,
                dst=True,
                label="Test Location",
            )

            # Verify params include timezone and dst
            call_kwargs = mock_get.call_args.kwargs
            assert call_kwargs["params"]["tz"] == "-5.0"
            assert call_kwargs["params"]["dst"] == "true"
            assert call_kwargs["params"]["label"] == "Test Location"

    @pytest.mark.asyncio
    async def test_get_solar_eclipse_by_date_success(self, provider):
        """Test successful solar eclipse by date API call."""
        mock_response_data = {
            "apiversion": "3.1.0",
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-74.0, 40.7, 100]},
            "properties": {
                "year": 2024,
                "month": 4,
                "day": 8,
                "event": "Total Solar Eclipse",
                "description": "Sun in Total Eclipse at this Location",
                "delta_t": "69.4",
                "local_data": [
                    {
                        "day": "8",
                        "phenomenon": "Eclipse Begins",
                        "time": "14:10:45.1",
                        "altitude": "45.2",
                        "azimuth": "145.3",
                    }
                ],
            },
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await provider.get_solar_eclipse_by_date(
                date="2024-04-08", latitude=40.7, longitude=-74.0, height=100
            )

            assert result.geometry.coordinates == [-74.0, 40.7, 100]
            assert result.properties.year == 2024

            # Verify API was called with correct params
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args.kwargs
            assert call_kwargs["params"]["date"] == "2024-04-08"
            assert call_kwargs["params"]["coords"] == "40.7,-74.0"
            assert call_kwargs["params"]["height"] == "100"

    @pytest.mark.asyncio
    async def test_get_solar_eclipse_invalid_height_min(self, provider):
        """Test solar eclipse with height below minimum."""
        with pytest.raises(ValueError, match="height must be between"):
            await provider.get_solar_eclipse_by_date(
                date="2024-04-08", latitude=40.7, longitude=-74.0, height=-300
            )

    @pytest.mark.asyncio
    async def test_get_solar_eclipse_invalid_height_max(self, provider):
        """Test solar eclipse with height above maximum."""
        with pytest.raises(ValueError, match="height must be between"):
            await provider.get_solar_eclipse_by_date(
                date="2024-04-08", latitude=40.7, longitude=-74.0, height=15000
            )

    @pytest.mark.asyncio
    async def test_get_solar_eclipses_by_year_success(self, provider):
        """Test successful solar eclipses by year API call."""
        mock_response_data = {
            "apiversion": "3.1.0",
            "year": 2024,
            "eclipses_in_year": [
                {
                    "year": 2024,
                    "month": 4,
                    "day": 8,
                    "event": "Total Solar Eclipse",
                },
                {
                    "year": 2024,
                    "month": 10,
                    "day": 2,
                    "event": "Annular Solar Eclipse",
                },
            ],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await provider.get_solar_eclipses_by_year(year=2024)

            assert result.year == 2024

            # Verify API was called with correct params
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args.kwargs
            assert call_kwargs["params"]["year"] == "2024"

    @pytest.mark.asyncio
    async def test_get_solar_eclipses_invalid_year_min(self, provider):
        """Test solar eclipses with year below minimum."""
        with pytest.raises(ValueError, match="year must be between"):
            await provider.get_solar_eclipses_by_year(year=1700)

    @pytest.mark.asyncio
    async def test_get_solar_eclipses_invalid_year_max(self, provider):
        """Test solar eclipses with year above maximum."""
        with pytest.raises(ValueError, match="year must be between"):
            await provider.get_solar_eclipses_by_year(year=2100)

    @pytest.mark.asyncio
    async def test_get_earth_seasons_success(self, provider):
        """Test successful earth seasons API call."""
        mock_response_data = {
            "apiversion": "3.1.0",
            "year": 2024,
            "tz": 0.0,
            "dst": False,
            "data": [
                {
                    "phenom": "Equinox",
                    "year": 2024,
                    "month": 3,
                    "day": 20,
                    "time": "03:06",
                },
                {
                    "phenom": "Solstice",
                    "year": 2024,
                    "month": 6,
                    "day": 20,
                    "time": "20:50",
                },
            ],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await provider.get_earth_seasons(year=2024)

            assert result.year == 2024
            assert len(result.data) == 2

            # Verify API was called with correct params
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args.kwargs
            assert call_kwargs["params"]["year"] == "2024"

    @pytest.mark.asyncio
    async def test_get_earth_seasons_with_timezone(self, provider):
        """Test earth seasons with timezone and DST parameters."""
        mock_response_data = {
            "apiversion": "3.1.0",
            "year": 2024,
            "tz": -5.0,
            "dst": True,
            "data": [],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            await provider.get_earth_seasons(year=2024, timezone=-5.0, dst=True)

            # Verify params include timezone and dst
            call_kwargs = mock_get.call_args.kwargs
            assert call_kwargs["params"]["tz"] == "-5.0"
            assert call_kwargs["params"]["dst"] == "true"

    @pytest.mark.asyncio
    async def test_get_earth_seasons_invalid_year_min(self, provider):
        """Test earth seasons with year below minimum."""
        with pytest.raises(ValueError, match="year must be between"):
            await provider.get_earth_seasons(year=1600)

    @pytest.mark.asyncio
    async def test_get_earth_seasons_invalid_year_max(self, provider):
        """Test earth seasons with year above maximum."""
        with pytest.raises(ValueError, match="year must be between"):
            await provider.get_earth_seasons(year=2200)
