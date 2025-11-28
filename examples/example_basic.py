"""Basic example usage of the US Navy Celestial MCP Server.

This example demonstrates how to use the server's tools directly in Python code.
"""

import asyncio

from chuk_mcp_celestial.server import (
    get_earth_seasons,
    get_moon_phases,
    get_solar_eclipse_by_date,
    get_solar_eclipses_by_year,
    get_sun_moon_data,
)


async def main():
    """Run basic examples of all celestial tools."""

    print("=" * 80)
    print("US Navy Celestial MCP Server - Basic Examples")
    print("=" * 80)
    print()

    # Example 1: Get moon phases
    print("1. Moon Phases")
    print("-" * 80)
    moon_phases = await get_moon_phases(date="2024-12-1", num_phases=8)
    print("Next 8 moon phases starting from 2024-12-01:")
    for phase in moon_phases.phasedata:
        print(f"  {phase.phase}: {phase.year}-{phase.month:02d}-{phase.day:02d} at {phase.time} UT")
    print()

    # Example 2: Get sun and moon data for a location
    print("2. Sun and Moon Rise/Set/Transit Times")
    print("-" * 80)
    seattle_lat, seattle_lon = 47.60, -122.33
    sun_moon = await get_sun_moon_data(
        date="2024-12-21",  # Winter solstice
        latitude=seattle_lat,
        longitude=seattle_lon,
        timezone=-8,  # PST
        dst=False,
    )
    data = sun_moon.properties.data
    print(f"Seattle, WA on {data.month}/{data.day}/{data.year} ({data.day_of_week}):")
    print(f"  Moon Phase: {data.curphase} ({data.fracillum} illuminated)")
    print("  Sun Events:")
    for event in data.sundata[:4]:  # First few events
        print(f"    {event.phen}: {event.time}")
    print("  Moon Events:")
    for event in data.moondata[:3]:  # First few events
        print(f"    {event.phen}: {event.time}")
    print()

    # Example 3: Check solar eclipse visibility
    print("3. Solar Eclipse Local Circumstances")
    print("-" * 80)
    eclipse = await get_solar_eclipse_by_date(
        date="2017-8-21",
        latitude=45.52,  # Portland, OR
        longitude=-122.67,
        height=15,
    )
    print(f"Eclipse: {eclipse.properties.event}")
    print("Location: Portland, OR")
    print(f"Description: {eclipse.properties.description}")
    if eclipse.properties.magnitude:
        print(f"Magnitude: {eclipse.properties.magnitude}")
        print(f"Obscuration: {eclipse.properties.obscuration}")
        print(f"Duration: {eclipse.properties.duration}")
        print("Local Events:")
        for event in eclipse.properties.local_data:
            print(f"  {event.phenomenon}: {event.time}")
            print(f"    Sun position: {event.altitude}° altitude, {event.azimuth}° azimuth")
    print()

    # Example 4: Find all eclipses in a year
    print("4. All Solar Eclipses in a Year")
    print("-" * 80)
    eclipses_2024 = await get_solar_eclipses_by_year(year=2024)
    print(f"Solar eclipses in {eclipses_2024.year}:")
    for eclipse in eclipses_2024.eclipses_in_year:
        print(f"  {eclipse.month:02d}/{eclipse.day:02d}/{eclipse.year}: {eclipse.event}")
    print()

    # Example 5: Get Earth's seasonal events
    print("5. Earth's Seasons and Orbital Events")
    print("-" * 80)
    seasons = await get_earth_seasons(year=2024, timezone=0)  # UTC
    print(f"Seasonal events for {seasons.year} (UTC):")
    for event in seasons.data:
        print(f"  {event.phenom}: {event.month:02d}/{event.day:02d}/{event.year} at {event.time}")
    print()

    print("=" * 80)
    print("All examples completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
