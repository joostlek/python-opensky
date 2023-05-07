"""Tests for the OpenSky Library."""
# pylint: disable=protected-access
import asyncio

import aiohttp
import pytest
from aiohttp import ClientError
from aresponses import Response, ResponsesMockServer

from opensky import (
    AircraftCategory,
    OpenSky,
    OpenSkyConnectionError,
    OpenSkyError,
    PositionSource,
    StatesResponse,
)

from . import load_fixture


async def test_states(
    aresponses: ResponsesMockServer,
) -> None:
    """Test retrieving states."""
    aresponses.add(
        "opensky-network.org",
        "/api/states/all",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("states.json"),
        ),
    )
    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        response: StatesResponse = await opensky.states()
        assert len(response.states) == 4
        assert response.time == 1683488744
        first_aircraft = response.states[0]
        assert first_aircraft.icao24 == "ab1644"
        assert first_aircraft.callsign == "UAL421  "
        assert first_aircraft.origin_country == "United States"
        assert first_aircraft.time_position == 1683488743
        assert first_aircraft.last_contact == 1683488743
        assert first_aircraft.longitude == -71.1656
        assert first_aircraft.latitude == 42.5372
        assert first_aircraft.barometric_altitude == 2217.42
        assert not first_aircraft.on_ground
        assert first_aircraft.velocity == 137.8
        assert first_aircraft.true_track == 342.17
        assert first_aircraft.vertical_rate == 13
        assert first_aircraft.sensors is None
        assert first_aircraft.geo_altitude == 2194.56
        assert first_aircraft.transponder_code is None
        assert not first_aircraft.special_purpose_indicator
        assert first_aircraft.position_source == PositionSource.ADSB
        assert first_aircraft.category == AircraftCategory.LARGE
        await opensky.close()


async def test_new_session(
    aresponses: ResponsesMockServer,
) -> None:
    """Test that it creates a new session if not given one."""
    aresponses.add(
        "opensky-network.org",
        "/api/states/all",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("states.json"),
        ),
    )
    async with OpenSky() as opensky:
        assert not opensky.session
        await opensky.states()
        assert opensky.session


async def test_timeout(aresponses: ResponsesMockServer) -> None:
    """Test request timeout."""

    # Faking a timeout by sleeping
    async def response_handler(_: aiohttp.ClientResponse) -> Response:
        """Response handler for this test."""
        await asyncio.sleep(2)
        return aresponses.Response(body="Goodmorning!")

    aresponses.add(
        "opensky-network.org",
        "/api/states/all",
        "GET",
        response_handler,
    )

    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session, request_timeout=1)
        with pytest.raises(OpenSkyConnectionError):
            assert await opensky.states()
        await opensky.close()


async def test_request_error(aresponses: ResponsesMockServer) -> None:
    """Test request error."""

    async def response_handler(_: aiohttp.ClientResponse) -> Response:
        """Response handler for this test."""
        raise ClientError

    aresponses.add(
        "opensky-network.org",
        "/api/states/all",
        "GET",
        response_handler,
    )

    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        with pytest.raises(OpenSkyConnectionError):
            assert await opensky.states()
        await opensky.close()


async def test_unexpected_server_response(
    aresponses: ResponsesMockServer,
) -> None:
    """Test handling a server error."""
    aresponses.add(
        "opensky-network.org",
        "/api/states/all",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "plain/text"},
            text="Yes",
        ),
    )

    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        with pytest.raises(OpenSkyError):
            assert await opensky.states()
        await opensky.close()
