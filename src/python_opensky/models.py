"""Asynchronous Python client for the OpenSky API."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .const import AircraftCategory, PositionSource
from .exceptions import OpenSkyCoordinateError
from .util import to_enum

if TYPE_CHECKING:
    from typing_extensions import Self


@dataclass(slots=True)
class StatesResponse:
    """Represents the states response."""

    states: list[StateVector]
    time: int

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Self:
        """Initialize from the API."""
        return cls(
            time=data["time"],
            states=[
                StateVector.from_api(vector_data) for vector_data in data["states"]
            ],
        )


@dataclass(slots=True)
# pylint: disable-next=too-many-instance-attributes
class StateVector:
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

    icao24: str
    callsign: str | None
    origin_country: str
    time_position: int | None
    last_contact: int
    longitude: float | None
    latitude: float | None
    geo_altitude: float | None
    on_ground: bool
    velocity: float | None
    true_track: float | None
    vertical_rate: float | None
    sensors: list[int] | None
    barometric_altitude: float | None
    transponder_code: str | None
    special_purpose_indicator: bool
    position_source: PositionSource
    category: AircraftCategory

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Self:
        """Initialize from the API."""
        return cls(
            icao24=data["icao24"],
            callsign=data.get("callsign"),
            origin_country=data["origin_country"],
            time_position=data.get("time_position"),
            last_contact=data["last_contact"],
            longitude=data.get("longitude"),
            latitude=data.get("latitude"),
            geo_altitude=data.get("geo_altitude"),
            on_ground=data["on_ground"],
            velocity=data.get("velocity"),
            true_track=data.get("true_track"),
            vertical_rate=data.get("vertical_rate"),
            sensors=data.get("sensors", []),
            barometric_altitude=data.get("baro_altitude"),
            transponder_code=data.get("squawk"),
            special_purpose_indicator=data["spi"],
            position_source=to_enum(
                PositionSource,
                data["position_source"],
                PositionSource.UNKNOWN,
            ),
            category=to_enum(
                AircraftCategory,
                data["category"],
                AircraftCategory.NO_INFORMATION,
            ),
        )


@dataclass(slots=True)
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
