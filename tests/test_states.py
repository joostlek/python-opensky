"""Tests for the OpenSky Library."""

import asyncio
from dataclasses import asdict
from typing import Any

import aiohttp
import pytest
from aiohttp import BasicAuth
from aiointercept import CallbackResult, aiointercept
from syrupy.assertion import SnapshotAssertion
from yarl import URL

from python_opensky import (
    BoundingBox,
    OpenSky,
    OpenSkyConnectionError,
    OpenSkyError,
    StatesResponse,
)
from python_opensky.exceptions import OpenSkyUnauthenticatedError

from . import load_fixture

OPENSKY_URL = "https://opensky-network.org/api"
STATES_URL = f"{OPENSKY_URL}/states/all?time=0&extended=true"
OWN_STATES_URL = f"{OPENSKY_URL}/states/own?time=0"
BOUNDING_BOX_STATES_URL = (
    f"{OPENSKY_URL}/states/all?time=0&extended=true&lamin=0&lamax=0&lomin=0&lomax=0"
)
# The authenticate() call probes the API with BoundingBox(0.0, 0.0, 1.0, 1.0).
AUTH_STATES_URL = (
    f"{OPENSKY_URL}/states/all"
    "?time=0&extended=true&lamin=0.0&lamax=0.0&lomin=1.0&lomax=1.0"
)


async def test_states(
    responses: aiointercept,
    snapshot: SnapshotAssertion,
) -> None:
    """Test retrieving states."""
    responses.get(
        STATES_URL,
        status=200,
        content_type="application/json",
        body=load_fixture("states.json"),
    )
    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        response: StatesResponse = await opensky.get_states()
        assert asdict(response) == snapshot
        await opensky.close()


async def test_unavailable_states(
    responses: aiointercept,
) -> None:
    """Test retrieving no states."""
    responses.get(
        STATES_URL,
        status=200,
        content_type="application/json",
        body=load_fixture("unavailable_states.json"),
    )
    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        response: StatesResponse = await opensky.get_states()
        assert response.states is not None
        assert len(response.states) == 0
        assert response.time == 1683488744
        await opensky.close()


async def test_own_states(
    responses: aiointercept,
) -> None:
    """Test retrieving own states."""
    responses.get(
        AUTH_STATES_URL,
        status=200,
        content_type="application/json",
        body=load_fixture("states.json"),
    )
    responses.get(
        OWN_STATES_URL,
        status=200,
        content_type="application/json",
        body=load_fixture("states.json"),
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
    responses: aiointercept,
) -> None:
    """Test retrieving no own states."""
    responses.get(
        AUTH_STATES_URL,
        status=200,
        content_type="application/json",
        body=load_fixture("states.json"),
    )
    responses.get(
        OWN_STATES_URL,
        status=200,
        content_type="application/json",
        body=load_fixture("unavailable_states.json"),
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
    responses: aiointercept,
) -> None:
    """Test retrieving states."""
    responses.get(
        BOUNDING_BOX_STATES_URL,
        status=200,
        content_type="application/json",
        body=load_fixture("states.json"),
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
    responses: aiointercept,
) -> None:
    """Test credit usage."""
    responses.get(
        STATES_URL,
        status=200,
        content_type="application/json",
        body=load_fixture("states.json"),
    )
    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        await opensky.get_states()
        assert opensky.remaining_credits() == opensky.opensky_credits - 4
        await opensky.close()


async def test_new_session(
    responses: aiointercept,
) -> None:
    """Test that it creates a new session if not given one."""
    responses.get(
        STATES_URL,
        status=200,
        content_type="application/json",
        body=load_fixture("states.json"),
    )
    async with OpenSky() as opensky:
        assert not opensky.session
        await opensky.get_states()
        assert opensky.session


async def test_timeout(responses: aiointercept) -> None:
    """Test request timeout."""

    # Faking a timeout by sleeping
    async def response_handler(_url: URL, **_kwargs: Any) -> CallbackResult:
        """Response handler for this test."""
        await asyncio.sleep(2)
        return CallbackResult(body="Goodmorning!")

    responses.get(STATES_URL, callback=response_handler)

    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session, request_timeout=1)
        with pytest.raises(OpenSkyConnectionError):
            assert await opensky.get_states()
        await opensky.close()


async def test_auth(responses: aiointercept) -> None:
    """Test request authentication."""

    def response_handler(_url: URL, **kwargs: Any) -> CallbackResult:
        """Response handler for this test."""
        headers = kwargs["headers"]
        assert headers["Authorization"]
        assert headers["Authorization"] == "Basic dGVzdDp0ZXN0"
        return CallbackResult(
            status=200,
            content_type="application/json",
            body=load_fixture("states.json"),
        )

    responses.get(AUTH_STATES_URL, callback=response_handler)
    responses.get(STATES_URL, callback=response_handler)

    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        await opensky.authenticate(BasicAuth(login="test", password="test"))
        await opensky.get_states()
        await opensky.close()


async def test_unauthorized(responses: aiointercept) -> None:
    """Test request authentication."""
    responses.get(
        AUTH_STATES_URL,
        status=401,
        content_type="application/json",
        body=load_fixture("states.json"),
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


async def test_user_credits(responses: aiointercept) -> None:
    """Test authenticated user credits."""
    responses.get(
        AUTH_STATES_URL,
        status=200,
        content_type="application/json",
        body=load_fixture("states.json"),
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


async def test_request_error(responses: aiointercept) -> None:
    """Test request error."""
    responses.get(STATES_URL, exception=True)

    async with aiohttp.ClientSession() as session:
        opensky = OpenSky(session=session)
        with pytest.raises(OpenSkyConnectionError):
            assert await opensky.get_states()
        await opensky.close()


async def test_unexpected_server_response(
    responses: aiointercept,
) -> None:
    """Test handling a server error."""
    responses.get(
        STATES_URL,
        status=200,
        content_type="plain/text",
        body="Yes",
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
