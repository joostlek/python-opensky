"""Asynchronous Python client for the OpenSky API."""

import asyncio

from opensky import OpenSky, StatesResponse


async def main() -> None:
    """Show example of fetching flight states from OpenSky."""
    async with OpenSky() as open_sky:
        states: StatesResponse = await open_sky.states()
        print(states)


if __name__ == "__main__":
    asyncio.run(main())
