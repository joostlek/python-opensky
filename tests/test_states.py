"""Tests for the OpenSky Library."""
import asyncio
from dataclasses import asdict

import aiohttp
import pytest
from aiohttp import BasicAuth, ClientError
from aiohttp.web_request import BaseRequest
from aresponses import Response, ResponsesMockServer
from syrupy.assertion import SnapshotAssertion

from python_opensky import (
    BoundingBox,
    OpenSky,
    OpenSkyConnectionError,
    OpenSkyError,
    StatesResponse,
)
from python_opensky.exceptions import OpenSkyUnauthenticatedError

from . import load_fixture

OPENSKY_URL = "opensky-network.org"


async def test_states(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
) -> None:
    """Test retrieving states."""
    aresponses.add(
        OPENSKY_URL,
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
        response: StatesResponse = await opensky.get_states()
        assert asdict(response) == snapshot
        await opensky.close()


async def test_unavailable_states(
    aresponses: ResponsesMockServer,
) -> None:
    """Test retrieving no states."""
    aresponses.add(
        OPENSKY_URL,
        "/api/states/all",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("unavailable_states.json"),
        ),
    )
    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        response: StatesResponse = await opensky.get_states()
        assert response.states is not None
        assert len(response.states) == 0
        assert response.time == 1683488744
        await opensky.close()


async def test_own_states(
    aresponses: ResponsesMockServer,
) -> None:
    """Test retrieving own states."""
    aresponses.add(
        OPENSKY_URL,
        "/api/states/all",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("states.json"),
        ),
    )
    aresponses.add(
        OPENSKY_URL,
        "/api/states/own",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("states.json"),
        ),
    )
    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        await opensky.authenticate(
            BasicAuth(login="test", password="test"),
            contributing_user=True,
        )
        response: StatesResponse = await opensky.get_own_states()
        assert len(response.states) == 4
        assert opensky.opensky_credits == 8000
        assert opensky.remaining_credits() == 7999
        await opensky.close()


async def test_unavailable_own_states(
    aresponses: ResponsesMockServer,
) -> None:
    """Test retrieving no own states."""
    aresponses.add(
        OPENSKY_URL,
        "/api/states/all",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("states.json"),
        ),
    )
    aresponses.add(
        OPENSKY_URL,
        "/api/states/own",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("unavailable_states.json"),
        ),
    )
    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        await opensky.authenticate(
            BasicAuth(login="test", password="test"),
            contributing_user=True,
        )
        response: StatesResponse = await opensky.get_own_states()
        assert response.states is not None
        assert len(response.states) == 0
        assert response.time == 1683488744
        await opensky.close()


async def test_states_with_bounding_box(
    aresponses: ResponsesMockServer,
) -> None:
    """Test retrieving states."""
    aresponses.add(
        OPENSKY_URL,
        "/api/states/all?time=0&extended=true&lamin=0&lamax=0&lomin=0&lomax=0",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("states.json"),
        ),
        match_querystring=True,
    )
    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        bounding_box = BoundingBox(
            min_latitude=0,
            max_latitude=0,
            min_longitude=0,
            max_longitude=0,
        )
        await opensky.get_states(bounding_box=bounding_box)
        await opensky.close()


async def test_credit_usage(
    aresponses: ResponsesMockServer,
) -> None:
    """Test credit usage."""
    aresponses.add(
        OPENSKY_URL,
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
        await opensky.get_states()
        assert opensky.remaining_credits() == opensky.opensky_credits - 4
        await opensky.close()


async def test_new_session(
    aresponses: ResponsesMockServer,
) -> None:
    """Test that it creates a new session if not given one."""
    aresponses.add(
        OPENSKY_URL,
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
        await opensky.get_states()
        assert opensky.session


async def test_timeout(aresponses: ResponsesMockServer) -> None:
    """Test request timeout."""

    # Faking a timeout by sleeping
    async def response_handler(_: BaseRequest) -> Response:
        """Response handler for this test."""
        await asyncio.sleep(2)
        return aresponses.Response(body="Goodmorning!")

    aresponses.add(
        OPENSKY_URL,
        "/api/states/all",
        "GET",
        response_handler,
    )

    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session, request_timeout=1)
        with pytest.raises(OpenSkyConnectionError):
            assert await opensky.get_states()
        await opensky.close()


async def test_auth(aresponses: ResponsesMockServer) -> None:
    """Test request authentication."""

    def response_handler(request: BaseRequest) -> Response:
        """Response handler for this test."""
        assert request.headers
        assert request.headers["Authorization"]
        assert request.headers["Authorization"] == "Basic dGVzdDp0ZXN0"
        return aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("states.json"),
        )

    aresponses.add(
        OPENSKY_URL,
        "/api/states/all",
        "GET",
        response_handler,
        repeat=2,
    )

    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        await opensky.authenticate(BasicAuth(login="test", password="test"))
        await opensky.get_states()
        await opensky.close()


async def test_unauthorized(aresponses: ResponsesMockServer) -> None:
    """Test request authentication."""
    aresponses.add(
        OPENSKY_URL,
        "/api/states/all",
        "GET",
        aresponses.Response(
            status=401,
            headers={"Content-Type": "application/json"},
            text=load_fixture("states.json"),
        ),
    )

    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        try:
            await opensky.authenticate(BasicAuth(login="test", password="test"))
            pytest.fail("Should've thrown exception")
        except OpenSkyUnauthenticatedError:
            pass
        assert opensky.is_authenticated is False
        await opensky.close()


async def test_user_credits(aresponses: ResponsesMockServer) -> None:
    """Test authenticated user credits."""
    aresponses.add(
        OPENSKY_URL,
        "/api/states/all",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixture("states.json"),
        ),
        repeat=2,
    )
    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        assert opensky.opensky_credits == 400
        await opensky.authenticate(BasicAuth(login="test", password="test"))
        assert opensky.opensky_credits == 4000
        await opensky.authenticate(
            BasicAuth(login="test", password="test"),
            contributing_user=True,
        )
        assert opensky.opensky_credits == 8000
        assert opensky.is_contributing_user is True
        await opensky.close()


async def test_request_error(aresponses: ResponsesMockServer) -> None:
    """Test request error."""

    async def response_handler(_: BaseRequest) -> Response:
        """Response handler for this test."""
        raise ClientError

    aresponses.add(
        OPENSKY_URL,
        "/api/states/all",
        "GET",
        response_handler,
    )

    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        with pytest.raises(OpenSkyConnectionError):
            assert await opensky.get_states()
        await opensky.close()


async def test_unexpected_server_response(
    aresponses: ResponsesMockServer,
) -> None:
    """Test handling a server error."""
    aresponses.add(
        OPENSKY_URL,
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
            assert await opensky.get_states()
        await opensky.close()


async def test_unauthenticated_own_states() -> None:
    """Test unauthenticated access to own states."""
    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        with pytest.raises(OpenSkyUnauthenticatedError):
            assert await opensky.get_own_states()
        await opensky.close()


async def test_calculating_credit_usage() -> None:
    """Test calculating credit usage."""
    opensky = OpenSky()
    bounding_box = BoundingBox(
        min_latitude=49.7,
        max_latitude=50.5,
        min_longitude=3.2,
        max_longitude=4.6,
    )
    assert opensky.calculate_credit_costs(bounding_box) == 1
    bounding_box = BoundingBox(
        min_latitude=46.5,
        max_latitude=49.9,
        min_longitude=-1.4,
        max_longitude=6.8,
    )
    assert opensky.calculate_credit_costs(bounding_box) == 2
    bounding_box = BoundingBox(
        min_latitude=42.2,
        max_latitude=49.8,
        min_longitude=-4.7,
        max_longitude=10.9,
    )
    assert opensky.calculate_credit_costs(bounding_box) == 3
    bounding_box = BoundingBox(
        min_latitude=42.2,
        max_latitude=49.8,
        min_longitude=-80.7,
        max_longitude=10.9,
    )
    assert opensky.calculate_credit_costs(bounding_box) == 4
