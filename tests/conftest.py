"""Pytest configuration and fixtures for chuk-mcp-celestial tests."""

import asyncio
from typing import Any, Callable

import pytest


# Coordinate fixtures for common test locations
@pytest.fixture
def seattle_coords() -> dict[str, float]:
    """Seattle, WA coordinates."""
    return {"latitude": 47.60, "longitude": -122.33}


@pytest.fixture
def portland_coords() -> dict[str, float]:
    """Portland, OR coordinates."""
    return {"latitude": 46.67, "longitude": -122.65}


@pytest.fixture
def greenwich_coords() -> dict[str, float]:
    """Greenwich, UK coordinates (Prime Meridian)."""
    return {"latitude": 51.48, "longitude": 0.0}


@pytest.fixture
def sydney_coords() -> dict[str, float]:
    """Sydney, Australia coordinates."""
    return {"latitude": -33.87, "longitude": 151.21}


# Network retry fixture for flaky API tests
@pytest.fixture
async def retry_on_network_error() -> Callable:
    """Retry a network operation with exponential backoff."""

    async def _retry(func: Callable, max_retries: int = 3, initial_delay: float = 1.0) -> Any:
        """Retry an async function with exponential backoff.

        Args:
            func: Async function to retry
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds (doubles each retry)

        Returns:
            Result from the function

        Raises:
            Last exception if all retries fail
        """
        delay = initial_delay
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff

        # If we get here, all retries failed
        raise last_exception  # type: ignore

    return _retry
