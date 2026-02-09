"""Constants for chuk-mcp-celestial server.

Planet name mappings, visibility thresholds, storage configuration,
and environment variable names.
"""

from enum import Enum


# ============================================================================
# Planet Skyfield Name Mapping
# ============================================================================

# Map our Planet enum values to Skyfield ephemeris names
PLANET_SKYFIELD_NAMES: dict[str, str] = {
    "Mercury": "mercury",
    "Venus": "venus",
    "Mars": "mars barycenter",
    "Jupiter": "jupiter barycenter",
    "Saturn": "saturn barycenter",
    "Uranus": "uranus barycenter",
    "Neptune": "neptune barycenter",
    "Pluto": "pluto barycenter",
}


# ============================================================================
# Planet Visibility Thresholds
# ============================================================================

# Minimum elongation (degrees from sun) for a planet to be potentially visible.
# Below this threshold the planet is lost in the sun's glare.
# Values are approximate and vary with atmospheric conditions.
PLANET_MIN_ELONGATION: dict[str, float] = {
    "Mercury": 10.0,  # Notoriously hard to see, needs > 10° elongation
    "Venus": 5.0,  # Bright enough to be seen at smaller elongations
    "Mars": 5.0,
    "Jupiter": 5.0,
    "Saturn": 5.0,
    "Uranus": 10.0,  # Dim, needs more separation
    "Neptune": 10.0,  # Very dim
    "Pluto": 15.0,  # Extremely dim
}

# Approximate absolute magnitude (H) for rough apparent magnitude estimation
# Used when Skyfield doesn't provide magnitude directly
PLANET_ABSOLUTE_MAGNITUDE: dict[str, float] = {
    "Mercury": -0.6,
    "Venus": -4.4,
    "Mars": -1.6,
    "Jupiter": -2.7,
    "Saturn": -0.5,
    "Uranus": 5.3,
    "Neptune": 7.8,
    "Pluto": 13.6,
}


# ============================================================================
# Storage Configuration (following tides pattern)
# ============================================================================


class StorageProvider(str, Enum):
    """Artifact storage provider types."""

    MEMORY = "memory"
    S3 = "s3"
    FILESYSTEM = "filesystem"


class SessionProvider(str, Enum):
    """Artifact session provider types."""

    MEMORY = "memory"
    REDIS = "redis"


class EnvVar:
    """Environment variable names used throughout the application."""

    # Artifact store
    ARTIFACTS_PROVIDER = "CHUK_ARTIFACTS_PROVIDER"
    BUCKET_NAME = "BUCKET_NAME"
    REDIS_URL = "REDIS_URL"
    ARTIFACTS_PATH = "CHUK_ARTIFACTS_PATH"
    AWS_ACCESS_KEY_ID = "AWS_ACCESS_KEY_ID"
    AWS_SECRET_ACCESS_KEY = "AWS_SECRET_ACCESS_KEY"
    AWS_ENDPOINT_URL_S3 = "AWS_ENDPOINT_URL_S3"

    # MCP transport
    MCP_STDIO = "MCP_STDIO"
