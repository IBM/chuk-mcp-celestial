#!/usr/bin/env python3
"""Example: Planet Position Queries

Demonstrates the get_planet_position tool for finding where planets are
in the sky at a specific time and location.

Requires: pip install "chuk-mcp-celestial[skyfield]"
"""

import asyncio
import os

# Use memory backend for ephemeris (no S3 needed)
os.environ.setdefault("SKYFIELD_STORAGE_BACKEND", "memory")

from chuk_mcp_celestial.server import get_planet_position


async def main():
    print("=" * 70)
    print("Planet Position Example")
    print("=" * 70)

    # Seattle coordinates
    lat, lon = 47.6, -122.3

    # 1. Where is Mars tonight?
    print("\n1. Where is Mars tonight? (Seattle, 10pm PDT)")
    print("-" * 70)
    result = await get_planet_position(
        planet="Mars",
        date="2025-6-15",
        time="22:00",
        latitude=lat,
        longitude=lon,
        timezone=-7,  # PDT
    )
    d = result.properties.data
    print(f"  Planet:        {d.planet.value}")
    print(
        f"  Altitude:      {d.altitude}° {'(above horizon)' if d.altitude > 0 else '(below horizon)'}"
    )
    print(f"  Azimuth:       {d.azimuth}° (0=N, 90=E, 180=S, 270=W)")
    print(f"  Distance:      {d.distance_au} AU ({d.distance_km:,.0f} km)")
    print(f"  Magnitude:     {d.magnitude} (lower = brighter)")
    print(f"  Illumination:  {d.illumination}%")
    print(f"  Constellation: {d.constellation}")
    print(f"  RA / Dec:      {d.right_ascension} / {d.declination}")
    print(f"  Elongation:    {d.elongation}° from Sun")
    print(f"  Visibility:    {d.visibility.value}")

    # 2. Survey all planets
    print("\n2. All Planets - Seattle, 10pm PDT")
    print("-" * 70)
    planets = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]

    print(f"  {'Planet':10s} {'Alt':>7s} {'Az':>7s} {'Mag':>6s} {'Const':>5s} {'Visibility'}")
    print(f"  {'-' * 10} {'-' * 7} {'-' * 7} {'-' * 6} {'-' * 5} {'-' * 17}")

    for planet in planets:
        r = await get_planet_position(
            planet=planet,
            date="2025-6-15",
            time="22:00",
            latitude=lat,
            longitude=lon,
            timezone=-7,
        )
        d = r.properties.data
        print(
            f"  {planet:10s} {d.altitude:+7.1f} {d.azimuth:7.1f} {d.magnitude:+6.1f} {d.constellation:>5s} {d.visibility.value}"
        )

    # 3. Track a planet across the night
    print("\n3. Mars Position Through the Night (Seattle)")
    print("-" * 70)
    print(f"  {'Time':>6s} {'Alt':>7s} {'Az':>7s} {'Visibility'}")
    print(f"  {'-' * 6} {'-' * 7} {'-' * 7} {'-' * 17}")

    for hour in range(18, 30):  # 6pm to 6am
        h = hour % 24
        r = await get_planet_position(
            planet="Mars",
            date="2025-6-15" if hour < 24 else "2025-6-16",
            time=f"{h:02d}:00",
            latitude=lat,
            longitude=lon,
        )
        d = r.properties.data
        print(f"  {h:02d}:00 {d.altitude:+7.1f} {d.azimuth:7.1f} {d.visibility.value}")

    # 4. Same planet from different cities
    print("\n4. Jupiter from Different Cities (midnight UTC)")
    print("-" * 70)
    cities = [
        ("Seattle", 47.6, -122.3),
        ("New York", 40.7, -74.0),
        ("London", 51.5, -0.1),
        ("Tokyo", 35.7, 139.7),
        ("Sydney", -33.9, 151.2),
    ]

    print(f"  {'City':12s} {'Alt':>7s} {'Az':>7s} {'Visibility'}")
    print(f"  {'-' * 12} {'-' * 7} {'-' * 7} {'-' * 17}")

    for city, city_lat, city_lon in cities:
        r = await get_planet_position(
            planet="Jupiter",
            date="2025-6-15",
            time="00:00",
            latitude=city_lat,
            longitude=city_lon,
        )
        d = r.properties.data
        print(f"  {city:12s} {d.altitude:+7.1f} {d.azimuth:7.1f} {d.visibility.value}")

    print("\n" + "=" * 70)
    print("Planet Position Example Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
