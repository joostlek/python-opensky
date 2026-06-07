"""Asynchronous Python client for the OpenSky API."""

from __future__ import annotations

import asyncio
import math
import socket
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from importlib import metadata
from typing import TYPE_CHECKING, Any, cast

from aiohttp import ClientError, ClientResponseError, ClientSession
from aiohttp.hdrs import METH_GET, METH_POST
from yarl import URL

from .const import (
    MAX_LATITUDE,
    MAX_LONGITUDE,
    MIN_LATITUDE,
    MIN_LONGITUDE,
    TOKEN_REFRESH_MARGIN,
    TOKEN_URL,
)
from .exceptions import (
    OpenSkyConnectionError,
    OpenSkyError,
    OpenSkyUnauthenticatedError,
)
from .models import BoundingBox, StatesResponse

if TYPE_CHECKING:
    from typing import Self


VERSION = metadata.version(__package__)


@dataclass
class _OAuthSession:
    """OAuth2 client credentials and the access token they hold."""

    client_id: str
    client_secret: str
    token: str | None = None
    expires_at: datetime | None = None


@dataclass
class OpenSky:
    """Main class for handling connections with OpenSky."""

    session: ClientSession | None = None
    request_timeout: int = 10
    api_host: str = "opensky-network.org"
    opensky_credits: int = 400
    timezone = UTC
    _close_session: bool = False
    _credit_usage: dict[datetime, int] = field(default_factory=dict)
    _oauth: _OAuthSession | None = None
    _contributing_user: bool = False

    async def authenticate(
        self,
        client_id: str,
        client_secret: str,
        *,
        contributing_user: bool = False,
    ) -> None:
        """Authenticate the user."""
        self._oauth = _OAuthSession(client_id=client_id, client_secret=client_secret)
        try:
            await self._refresh_token()
            await self.get_states(bounding_box=BoundingBox(0.0, 0.0, 1.0, 1.0))
        except OpenSkyUnauthenticatedError as exc:
            self._oauth = None
            raise OpenSkyUnauthenticatedError from exc
        self._contributing_user = contributing_user
        if contributing_user:
            self.opensky_credits = 8000
        else:
            self.opensky_credits = 4000

    @property
    def is_contributing_user(self) -> bool:
        """Return if the user is contributing to OpenSky."""
        return self._contributing_user

    @property
    def is_authenticated(self) -> bool:
        """Return if the user is correctly authenticated."""
        return self._oauth is not None

    async def _refresh_token(self) -> None:
        """Refresh the OAuth2 access token."""
        assert self._oauth is not None  # noqa: S101 — callers guard
        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.request(
                    METH_POST,
                    TOKEN_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self._oauth.client_id,
                        "client_secret": self._oauth.client_secret,
                    },
                )
        except TimeoutError as exception:
            msg = "Timeout occurred while connecting to the OpenSky API"
            raise OpenSkyConnectionError(msg) from exception
        except (
            ClientError,
            ClientResponseError,
            socket.gaierror,
        ) as exception:
            msg = "Error occurred while communicating with OpenSky API"
            raise OpenSkyConnectionError(msg) from exception

        if response.status == 401:
            raise OpenSkyUnauthenticatedError

        try:
            response.raise_for_status()
        except ClientResponseError as exception:
            msg = "Error occurred while communicating with OpenSky API"
            raise OpenSkyConnectionError(msg) from exception

        token_data = await response.json()
        self._oauth.token = token_data["access_token"]
        self._oauth.expires_at = datetime.now(UTC) + timedelta(
            seconds=token_data["expires_in"] - TOKEN_REFRESH_MARGIN,
        )

    async def _get_access_token(self) -> str | None:
        """Get a valid access token, refreshing if needed."""
        if self._oauth is None:
            return None
        if (
            self._oauth.token
            and self._oauth.expires_at
            and self._oauth.expires_at > datetime.now(UTC)
        ):
            return self._oauth.token
        await self._refresh_token()
        return self._oauth.token

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
            OpenSkyError: Received an unexpected response from the OpenSky API.

        """
        url = URL.build(
            scheme="https",
            host=self.api_host,
            port=443,
            path="/api/",
        ).joinpath(uri)

        headers = {
            "User-Agent": f"PythonOpenSky/{VERSION}",
            "Accept": "application/json, text/plain, */*",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        token = await self._get_access_token()
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.request(
                    METH_GET,
                    url.with_query(data),
                    headers=headers,
                )
                response.raise_for_status()
        except TimeoutError as exception:
            msg = "Timeout occurred while connecting to the OpenSky API"
            raise OpenSkyConnectionError(msg) from exception
        except (
            ClientError,
            ClientResponseError,
            socket.gaierror,
        ) as exception:
            if isinstance(exception, ClientResponseError) and exception.status == 401:
                raise OpenSkyUnauthenticatedError from exception
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

        return cast("dict[str, Any]", await response.json())

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

        if data["states"] is None:
            data["states"] = []
        else:
            data = {
                **data,
                "states": [self._convert_state(state) for state in data["states"]],
            }

        self._register_credit_usage(credit_cost)

        return StatesResponse.from_api(data)

    async def get_own_states(self, time: int = 0) -> StatesResponse:
        """Retrieve state vectors from your own sensors."""
        if self._oauth is None:
            raise OpenSkyUnauthenticatedError
        params = {
            "time": time,
        }

        data = await self._request("states/own", data=params)

        if data["states"] is None:
            data["states"] = []
        else:
            data = {
                **data,
                "states": [self._convert_state(state) for state in data["states"]],
            }

        return StatesResponse.from_api(data)

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
    def get_bounding_box(
        latitude: float,
        longitude: float,
        radius: float,
    ) -> BoundingBox:
        """Get bounding box from radius and a point."""
        half_side_in_km = abs(radius) / 1000

        lat = math.radians(latitude)
        lon = math.radians(longitude)

        approx_earth_radius = 6371
        hypotenuse_distance = math.sqrt(2 * (math.pow(half_side_in_km, 2)))

        lat_min = math.asin(
            math.sin(lat) * math.cos(hypotenuse_distance / approx_earth_radius)
            + math.cos(lat)
            * math.sin(hypotenuse_distance / approx_earth_radius)
            * math.cos(225 * (math.pi / 180)),
        )
        lon_min = lon + math.atan2(
            math.sin(225 * (math.pi / 180))
            * math.sin(hypotenuse_distance / approx_earth_radius)
            * math.cos(lat),
            math.cos(hypotenuse_distance / approx_earth_radius)
            - math.sin(lat) * math.sin(lat_min),
        )

        lat_max = math.asin(
            math.sin(lat) * math.cos(hypotenuse_distance / approx_earth_radius)
            + math.cos(lat)
            * math.sin(hypotenuse_distance / approx_earth_radius)
            * math.cos(45 * (math.pi / 180)),
        )
        lon_max = lon + math.atan2(
            math.sin(45 * (math.pi / 180))
            * math.sin(hypotenuse_distance / approx_earth_radius)
            * math.cos(lat),
            math.cos(hypotenuse_distance / approx_earth_radius)
            - math.sin(lat) * math.sin(lat_max),
        )

        rad2deg = math.degrees

        return BoundingBox(
            min_latitude=rad2deg(lat_min),
            max_latitude=rad2deg(lat_max),
            min_longitude=rad2deg(lon_min),
            max_longitude=rad2deg(lon_max),
        )

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns
        -------
            The OpenSky object.

        """
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.

        """
        await self.close()
