#!/usr/bin/env python3
"""Example: Planet Rise/Set/Transit Events

Demonstrates the get_planet_events tool for finding when planets
rise, transit (highest point), and set at a location.

Requires: pip install "chuk-mcp-celestial[skyfield]"
"""

import asyncio
import os

# Use memory backend for ephemeris (no S3 needed)
os.environ.setdefault("SKYFIELD_STORAGE_BACKEND", "memory")

from chuk_mcp_celestial.server import get_planet_events


async def main():
    print("=" * 70)
    print("Planet Events (Rise / Set / Transit) Example")
    print("=" * 70)

    # Seattle coordinates
    lat, lon = 47.6, -122.3

    # 1. When does Jupiter rise and set?
    print("\n1. Jupiter Rise/Set/Transit - Seattle, Jun 15 2025")
    print("-" * 70)
    result = await get_planet_events(
        planet="Jupiter",
        date="2025-6-15",
        latitude=lat,
        longitude=lon,
    )
    d = result.properties.data
    print(f"  Planet:        {d.planet.value}")
    print(f"  Date:          {d.date}")
    print(f"  Constellation: {d.constellation}")
    print(f"  Magnitude:     {d.magnitude}")
    if d.events:
        print("  Events (UTC):")
        for event in d.events:
            print(f"    {event.phen:15s} {event.time}")
    else:
        print("  No events (planet may not rise/set on this day)")

    # 2. Events in local time
    print("\n2. Mars Events in Local Time (Seattle, PDT = UTC-7)")
    print("-" * 70)
    result = await get_planet_events(
        planet="Mars",
        date="2025-6-15",
        latitude=lat,
        longitude=lon,
        timezone=-8,
        dst=True,  # PDT = PST(-8) + DST(+1) = -7
    )
    d = result.properties.data
    print(f"  Planet:        {d.planet.value}")
    print(f"  Constellation: {d.constellation}")
    print(f"  Magnitude:     {d.magnitude}")
    if d.events:
        print("  Events (PDT):")
        for event in d.events:
            print(f"    {event.phen:15s} {event.time}")
    else:
        print("  No events on this day")

    # 3. All planets rise/set for one day
    print("\n3. All Planets - Rise/Set/Transit (Seattle, UTC)")
    print("-" * 70)
    planets = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]

    for planet in planets:
        result = await get_planet_events(
            planet=planet,
            date="2025-6-15",
            latitude=lat,
            longitude=lon,
        )
        d = result.properties.data
        events_str = ", ".join(f"{e.phen} {e.time}" for e in d.events) if d.events else "no events"
        print(f"  {planet:8s} (mag {d.magnitude:+5.1f}, {d.constellation:3s}): {events_str}")

    # 4. Saturn events from London with BST
    print("\n4. Saturn Events - London (BST = UTC+1)")
    print("-" * 70)
    result = await get_planet_events(
        planet="Saturn",
        date="2025-6-15",
        latitude=51.5,
        longitude=-0.1,
        timezone=0,
        dst=True,  # BST = UTC + 1 hour DST
    )
    d = result.properties.data
    print(f"  Planet:        {d.planet.value}")
    print(f"  Constellation: {d.constellation}")
    if d.events:
        print("  Events (BST):")
        for event in d.events:
            print(f"    {event.phen:15s} {event.time}")

    # 5. Venus as morning/evening star
    print("\n5. Venus Events - Is it a Morning or Evening Star?")
    print("-" * 70)
    result = await get_planet_events(
        planet="Venus",
        date="2025-6-15",
        latitude=lat,
        longitude=lon,
    )
    d = result.properties.data
    if d.events:
        rise_times = [e for e in d.events if e.phen == "Rise"]
        set_times = [e for e in d.events if e.phen == "Set"]
        if rise_times and set_times:
            rise_h = int(rise_times[0].time.split(":")[0])
            set_h = int(set_times[0].time.split(":")[0])
            if rise_h < 12 and set_h < 18:
                star_type = "Morning Star (rises before noon, sets before evening)"
            else:
                star_type = "Evening Star (visible after sunset)"
            print(f"  Venus is the: {star_type}")
        for event in d.events:
            print(f"    {event.phen:15s} {event.time} UTC")
    else:
        print("  No events")

    print("\n" + "=" * 70)
    print("Planet Events Example Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
