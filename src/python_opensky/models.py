"""Asynchronous Python client for the OpenSky API."""
from __future__ import annotations

from pydantic import BaseModel, Field

from .const import AircraftCategory, PositionSource


class StatesResponse(BaseModel):
    """Represents the states response."""

    states: list[StateVector] = Field(...)
    time: int = Field(...)


class StateVector(BaseModel):
    """Represents the state of a vehicle at a particular time.

    Attributes
    ----------
    icao24: ICAO24 address of the transmitter in hex string representation.
    callsign: Callsign of the vehicle.
    origin_country: Inferred through the ICAO24 address.
    time_position: Seconds since epoch of last position report. Can be None if there
     was no position report received by OpenSky within 15s before.
    last_contact: Seconds since epoch of last received message from this transponder.
    longitude: In ellipsoidal coordinates (WGS-84) and degrees.
    latitude: In ellipsoidal coordinates (WGS-84) and degrees.
    geo_altitude: Geometric altitude in meters.
    on_ground: True if aircraft is on ground (sends ADS-B surface position reports).
    velocity: Over ground in m/s.
    true_track: In decimal degrees (0 is north).
    vertical_rate: In m/s, incline is positive, decline negative.
    sensors: Serial numbers of sensors which received messages from the vehicle within
     the validity period of this state vector.
    barometric_altitude: Barometric altitude in meters.
    transponder_code: Transponder code aka Squawk.
    special_purpose_indicator: Special purpose indicator.
    position_source: Origin of this state's position.
    category: Aircraft category.
    """

    icao24: str = Field(...)
    callsign: str | None = Field(None)
    origin_country: str = Field(...)
    time_position: int | None = Field(None)
    last_contact: int = Field(...)
    longitude: float | None = Field(None)
    latitude: float | None = Field(None)
    geo_altitude: float | None = Field(None)
    on_ground: bool = Field(...)
    velocity: float | None = Field(None)
    true_track: float | None = Field(None)
    vertical_rate: float | None = Field(None)
    sensors: list[int] | None = Field([])
    barometric_altitude: float | None = Field(None, alias="baro_altitude")
    transponder_code: str | None = Field(None, alias="squawk")
    special_purpose_indicator: bool = Field(..., alias="spi")
    position_source: PositionSource = Field(...)
    category: AircraftCategory = Field(...)


class BoundingBox(BaseModel):
    """Bounding box for retrieving state vectors."""

    min_latitude: float = Field(...)
    max_latitude: float = Field(...)
    min_longitude: float = Field(...)
    max_longitude: float = Field(...)


StatesResponse.update_forward_refs()
StateVector.update_forward_refs()
BoundingBox.update_forward_refs()
