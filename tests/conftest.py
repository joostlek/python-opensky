"""Fixtures for the OpenSky tests."""

from collections.abc import AsyncGenerator

import pytest
from aiointercept import aiointercept


@pytest.fixture(name="responses")
async def aiointercept_fixture() -> AsyncGenerator[aiointercept]:
    """Return aiointercept fixture."""
    async with aiointercept(mock_external_urls=True) as mocked_responses:
        yield mocked_responses
