"""Asynchronous Python client for the OpenSky API."""
from enum import Enum


class PositionSource(int, Enum):
    """Enum holding the Position source."""

    ADSB = 0
    ASTERIX = 1
    MLAT = 2
    FLARM = 3


class AircraftCategory(int, Enum):
    """Enum holding the aircraft category."""

    NO_INFORMATION = 0
    NO_ADS_INFORMATION = 1
    LIGHT = 2
    SMALL = 3
    LARGE = 4
    HIGH_VORTEX_LARGE = 5
    HEAVY = 6
    HIGH_PERFORMANCE = 7
    ROTORCRAFT = 8
    GLIDER = 9
    LIGHTER_THAN_AIR = 10
    PARACHUTIST = 11
    ULTRALIGHT = 12
    RESERVED = 13
    UNMANNED_AERIAL_VEHICLE = 14
    SPACE_VEHICLE = 15
    EMERGENCY_VEHICLE = 16
    SERVICE_VEHICLE = 17
    POINT_OBSTACLE = 18
    CLUSTER_OBSTACLE = 19
    LINE_OBSTACLE = 20


MIN_LATITUDE = "lamin"
MAX_LATITUDE = "lamax"
MIN_LONGITUDE = "lomin"
MAX_LONGITUDE = "lomax"
