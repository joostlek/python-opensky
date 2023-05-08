"""Asynchronous Python client for the OpenSky API."""
from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from importlib import metadata
from typing import Any, cast

import async_timeout
from aiohttp import ClientError, ClientResponseError, ClientSession
from aiohttp.hdrs import METH_GET
from yarl import URL

from .const import MAX_LATITUDE, MAX_LONGITUDE, MIN_LATITUDE, MIN_LONGITUDE
from .exceptions import OpenSkyConnectionError, OpenSkyError
from .models import BoundingBox, StatesResponse


@dataclass
class OpenSky:
    """Main class for handling connections with OpenSky."""

    session: ClientSession | None = None
    request_timeout: int = 10
    api_host: str = "python_opensky-network.org"
    opensky_credits: int = 400
    timezone = timezone.utc
    _close_session: bool = False
    _credit_usage: dict[datetime, int] = field(default_factory=dict)

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

    async def states(self, bounding_box: BoundingBox | None = None) -> StatesResponse:
        """Retrieve state vectors for a given time."""
        credit_costs = 4
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
            credit_costs = self.calculate_credit_costs(bounding_box)

        data = await self._request("states/all", data=params)

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

        data = {
            **data,
            "states": [dict(zip(keys, state, strict=True)) for state in data["states"]],
        }

        self._register_credit_usage(credit_costs)

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
