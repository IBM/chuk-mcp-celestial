"""Eclipse planning example.

This example shows how to find upcoming solar eclipses and check their visibility
from multiple locations.
"""

import asyncio

from chuk_mcp_celestial.server import (
    get_solar_eclipse_by_date,
    get_solar_eclipses_by_year,
)


async def check_eclipse_visibility(date: str, locations: dict[str, tuple[float, float]]):
    """Check eclipse visibility from multiple locations.

    Args:
        date: Eclipse date in YYYY-MM-DD format
        locations: Dictionary mapping location names to (latitude, longitude) tuples
    """
    print(f"\nEclipse Visibility Check for {date}")
    print("=" * 80)

    for name, (lat, lon) in locations.items():
        try:
            eclipse = await get_solar_eclipse_by_date(date=date, latitude=lat, longitude=lon)
        except Exception as exc:
            print(f"\n{name} ({lat}°, {lon}°):")
            print(f"  Error: {exc}")
            continue

        props = eclipse.properties

        print(f"\n{name} ({lat}°, {lon}°):")
        print(f"  Status: {props.description}")

        if "No Eclipse" not in props.description:
            print(f"  Magnitude: {props.magnitude}")
            print(f"  Obscuration: {props.obscuration}")
            print(f"  Duration: {props.duration}")

            # Find maximum eclipse
            for event in props.local_data:
                if "Maximum" in event.phenomenon:
                    print(
                        f"  Maximum at: {event.time} (altitude {event.altitude}°,"
                        f" azimuth {event.azimuth}°)"
                    )
                    break


async def find_next_eclipses(start_year: int, num_years: int = 5):
    """Find all solar eclipses in the next N years.

    Args:
        start_year: Starting year
        num_years: Number of years to check
    """
    print(f"\nSolar Eclipses from {start_year} to {start_year + num_years - 1}")
    print("=" * 80)

    all_eclipses = []

    for year in range(start_year, start_year + num_years):
        result = await get_solar_eclipses_by_year(year=year)
        for eclipse in result.eclipses_in_year:
            all_eclipses.append(
                {
                    "date": f"{eclipse.year}-{eclipse.month:02d}-{eclipse.day:02d}",
                    "event": eclipse.event,
                }
            )

    for eclipse in all_eclipses:
        print(f"{eclipse['date']}: {eclipse['event']}")

    return all_eclipses


async def main():
    """Run eclipse planning examples."""

    print("=" * 80)
    print("Solar Eclipse Planning Tool")
    print("=" * 80)

    # Find all eclipses in the next 5 years
    await find_next_eclipses(start_year=2024, num_years=5)

    # Check visibility of the 2024 April eclipse from major US cities
    us_cities = {
        "New York, NY": (40.71, -74.01),
        "Los Angeles, CA": (34.05, -118.24),
        "Chicago, IL": (41.88, -87.63),
        "Dallas, TX": (32.78, -96.80),
        "Miami, FL": (25.76, -80.19),
        "Seattle, WA": (47.60, -122.33),
    }

    # Check the April 2024 total solar eclipse
    await check_eclipse_visibility(date="2024-4-8", locations=us_cities)

    # Check a future eclipse
    print("\n")
    await check_eclipse_visibility(date="2027-8-2", locations=us_cities)


if __name__ == "__main__":
    asyncio.run(main())
