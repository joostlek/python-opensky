"""Asynchronous Python client for the OpenSky API."""
from __future__ import annotations

import asyncio
import math
import socket
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from importlib import metadata
from typing import Any, cast

import async_timeout
from aiohttp import BasicAuth, ClientError, ClientResponseError, ClientSession
from aiohttp.hdrs import METH_GET
from yarl import URL

from .const import MAX_LATITUDE, MAX_LONGITUDE, MIN_LATITUDE, MIN_LONGITUDE
from .exceptions import (
    OpenSkyConnectionError,
    OpenSkyError,
    OpenSkyUnauthenticatedError,
)
from .models import BoundingBox, StatesResponse


@dataclass
class OpenSky:
    """Main class for handling connections with OpenSky."""

    session: ClientSession | None = None
    request_timeout: int = 10
    api_host: str = "opensky-network.org"
    opensky_credits: int = 400
    timezone = timezone.utc
    _close_session: bool = False
    _credit_usage: dict[datetime, int] = field(default_factory=dict)
    _auth: BasicAuth | None = None
    _contributing_user: bool = False

    def authenticate(self, auth: BasicAuth, *, contributing_user: bool = False) -> None:
        """Authenticate the user."""
        self._auth = auth
        self._contributing_user = contributing_user
        if contributing_user:
            self.opensky_credits = 8000
        else:
            self.opensky_credits = 4000

    async def _request(
        self,
        uri: str,
        *,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Handle a request to OpenSky.

        A generic method for sending/handling HTTP requests done against
        OpenSky.

        Args:
        ----
            uri: the path to call.
            data: the query parameters to add.

        Returns:
        -------
            A Python dictionary (JSON decoded) with the response from
            the API.

        Raises:
        ------
            OpenSkyConnectionError: An error occurred while communicating with
                the OpenSky API.
            OpenSkyrror: Received an unexpected response from the OpenSky API.
        """
        version = metadata.version(__package__)
        url = URL.build(
            scheme="https",
            host=self.api_host,
            port=443,
            path="/api/",
        ).joinpath(uri)

        headers = {
            "User-Agent": f"PythonOpenSky/{version}",
            "Accept": "application/json, text/plain, */*",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with async_timeout.timeout(self.request_timeout):
                response = await self.session.request(
                    METH_GET,
                    url.with_query(data),
                    auth=self._auth,
                    headers=headers,
                )
                response.raise_for_status()
        except asyncio.TimeoutError as exception:
            msg = "Timeout occurred while connecting to the OpenSky API"
            raise OpenSkyConnectionError(msg) from exception
        except (
            ClientError,
            ClientResponseError,
            socket.gaierror,
        ) as exception:
            msg = "Error occurred while communicating with OpenSky API"
            raise OpenSkyConnectionError(msg) from exception

        content_type = response.headers.get("Content-Type", "")

        if "application/json" not in content_type:
            text = await response.text()
            msg = "Unexpected response from the OpenSky API"
            raise OpenSkyError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        return cast(dict[str, Any], await response.json())

    async def get_states(
        self,
        bounding_box: BoundingBox | None = None,
    ) -> StatesResponse:
        """Retrieve state vectors for a given time."""
        credit_cost = 4
        params = {
            "time": 0,
            "extended": "true",
        }

        if bounding_box:
            bounding_box.validate()
            params[MIN_LATITUDE] = bounding_box.min_latitude
            params[MAX_LATITUDE] = bounding_box.max_latitude
            params[MIN_LONGITUDE] = bounding_box.min_longitude
            params[MAX_LONGITUDE] = bounding_box.max_longitude
            credit_cost = self.calculate_credit_costs(bounding_box)

        data = await self._request("states/all", data=params)

        data = {
            **data,
            "states": [self._convert_state(state) for state in data["states"]],
        }

        self._register_credit_usage(credit_cost)

        return StatesResponse.parse_obj(data)

    async def get_own_states(self, time: int = 0) -> StatesResponse:
        """Retrieve state vectors from your own sensors."""
        if not self._auth:
            raise OpenSkyUnauthenticatedError
        params = {
            "time": time,
        }

        data = await self._request("states/own", data=params)

        data = {
            **data,
            "states": [self._convert_state(state) for state in data["states"]],
        }

        return StatesResponse.parse_obj(data)

    @staticmethod
    def calculate_credit_costs(bounding_box: BoundingBox) -> int:
        """Calculate the amount of credits a request costs."""
        latitude_degrees = bounding_box.max_latitude - bounding_box.min_latitude
        longitude_degrees = bounding_box.max_longitude - bounding_box.min_longitude
        area = latitude_degrees * longitude_degrees
        if area < 25:
            return 1
        if area < 100:
            return 2
        if area < 400:
            return 3
        return 4

    def _register_credit_usage(self, opensky_credits: int) -> None:
        self._credit_usage[datetime.now(self.timezone)] = opensky_credits

    def remaining_credits(self) -> int:
        """Calculate the remaining opensky credits."""
        now = datetime.now(self.timezone)
        used_credits = sum(
            v
            for k, v in self._credit_usage.items()
            if now - timedelta(hours=24) <= k <= now
        )
        return self.opensky_credits - used_credits

    @staticmethod
    def _convert_state(state: list[Any]) -> dict[str, Any]:
        keys = [
            "icao24",
            "callsign",
            "origin_country",
            "time_position",
            "last_contact",
            "longitude",
            "latitude",
            "baro_altitude",
            "on_ground",
            "velocity",
            "true_track",
            "vertical_rate",
            "sensors",
            "geo_altitude",
            "squawk",
            "spi",
            "position_source",
            "category",
        ]

        return dict(zip(keys, state, strict=True))

    @staticmethod
    # pylint: disable=too-many-locals
    def calculate_point(
        latitude: float,
        longitude: float,
        distance: float,
        degrees: float,
    ) -> tuple[float, float]:
        """Calculate a point from an origin point, direction in degrees and distance."""
        # ruff: noqa: N806
        # pylint: disable=invalid-name
        pi_d4 = math.atan(1.0)
        two_pi = pi_d4 * 8.0
        latitude = latitude * pi_d4 / 45.0
        longitude = longitude * pi_d4 / 45.0
        degrees = degrees * pi_d4 / 45.0
        if degrees < 0.0:
            degrees = degrees + two_pi
        if degrees > two_pi:
            degrees = degrees - two_pi
        axis_a = 6378137
        flattening = 1 / 298.257223563
        axis_b = axis_a * (1.0 - flattening)
        tan_u1 = (1 - flattening) * math.tan(latitude)
        u1 = math.atan(tan_u1)
        sigma1 = math.atan2(tan_u1, math.cos(degrees))
        sinalpha = math.cos(u1) * math.sin(degrees)
        cosalpha_sq = 1.0 - sinalpha * sinalpha
        u2 = cosalpha_sq * (axis_a * axis_a - axis_b * axis_b) / (axis_b * axis_b)
        A = 1.0 + (u2 / 16384) * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
        B = (u2 / 1024) * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
        # Starting with the approx
        sigma = distance / (axis_b * A)
        last_sigma = 2.0 * sigma + 2.0  # something impossible

        # Iterate the following 3 eqs until no sig change in sigma
        # two_sigma_m , delta_sigma
        while abs((last_sigma - sigma) / sigma) > 1.0e-9:
            two_sigma_m = 2 * sigma1 + sigma
            delta_sigma = (
                B
                * math.sin(sigma)
                * (
                    math.cos(two_sigma_m)
                    + (B / 4)
                    * (
                        math.cos(sigma)
                        * (
                            -1
                            + 2 * math.pow(math.cos(two_sigma_m), 2)
                            - (B / 6)
                            * math.cos(two_sigma_m)
                            * (-3 + 4 * math.pow(math.sin(sigma), 2))
                            * (-3 + 4 * math.pow(math.cos(two_sigma_m), 2))
                        )
                    )
                )
            )
            last_sigma = sigma
            sigma = (distance / (axis_b * A)) + delta_sigma
        phi2 = math.atan2(
            (
                math.sin(u1) * math.cos(sigma)
                + math.cos(u1) * math.sin(sigma) * math.cos(degrees)
            ),
            (
                (1 - flattening)
                * math.sqrt(
                    math.pow(sinalpha, 2)
                    + pow(
                        math.sin(u1) * math.sin(sigma)
                        - math.cos(u1) * math.cos(sigma) * math.cos(degrees),
                        2,
                    ),
                )
            ),
        )
        lembda = math.atan2(
            (math.sin(sigma) * math.sin(degrees)),
            (
                math.cos(u1) * math.cos(sigma)
                - math.sin(u1) * math.sin(sigma) * math.cos(degrees)
            ),
        )
        C = (flattening / 16) * cosalpha_sq * (4 + flattening * (4 - 3 * cosalpha_sq))
        omega = lembda - (1 - C) * flattening * sinalpha * (
            sigma
            + C
            * math.sin(sigma)
            * (
                math.cos(two_sigma_m)
                + C * math.cos(sigma) * (-1 + 2 * math.pow(math.cos(two_sigma_m), 2))
            )
        )
        lembda2 = longitude + omega
        math.atan2(
            sinalpha,
            (
                -math.sin(u1) * math.sin(sigma)
                + math.cos(u1) * math.cos(sigma) * math.cos(degrees)
            ),
        )
        phi2 = phi2 * 45.0 / pi_d4
        lembda2 = lembda2 * 45.0 / pi_d4
        return phi2, lembda2

    @staticmethod
    def get_bounding_box(
        latitude: float,
        longitude: float,
        radius: float,
    ) -> BoundingBox:
        """Get bounding box from radius and a point."""
        north = OpenSky.calculate_point(latitude, longitude, radius, 0)
        east = OpenSky.calculate_point(latitude, longitude, radius, 90)
        south = OpenSky.calculate_point(latitude, longitude, radius, 180)
        west = OpenSky.calculate_point(latitude, longitude, radius, 270)
        return BoundingBox(
            min_latitude=min(north[0], south[0]) + latitude,
            max_latitude=max(north[0], south[0]) + latitude,
            min_longitude=min(east[1], west[1]) + longitude,
            max_longitude=max(east[1], west[1]) + longitude,
        )

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> OpenSky:
        """Async enter.

        Returns
        -------
            The OpenSky object.
        """
        return self

    async def __aexit__(self, *_exc_info: Any) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.
        """
        await self.close()
