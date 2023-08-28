"""Asynchronous Python client for the OpenSky API."""
from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field

from .const import AircraftCategory, PositionSource
from .exceptions import OpenSkyCoordinateError


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


@dataclass
class BoundingBox:
    """Bounding box for retrieving state vectors."""

    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float

    def validate(self) -> None:
        """Validate if the latitude and longitude are correct."""
        self._check_latitude(self.min_latitude)
        self._check_latitude(self.max_latitude)
        self._check_longitude(self.min_longitude)
        self._check_longitude(self.max_longitude)

    @staticmethod
    def _check_latitude(degrees: float) -> None:
        if degrees < -90 or degrees > 90:
            msg = f"Invalid latitude {degrees}! Must be in [-90, 90]."
            raise OpenSkyCoordinateError(msg)

    @staticmethod
    def _check_longitude(degrees: float) -> None:
        if degrees < -180 or degrees > 180:
            msg = f"Invalid longitude {degrees}! Must be in [-180, 180]."
            raise OpenSkyCoordinateError(msg)


StatesResponse.update_forward_refs()
StateVector.update_forward_refs()
