"""Asynchronous Python client for the OpenSky API."""

import asyncio

from python_opensky import OpenSky, StatesResponse


async def main() -> None:
    """Show example of fetching flight states from OpenSky."""
    async with OpenSky() as opensky:
        states: StatesResponse = await opensky.get_states()
        print(states)


if __name__ == "__main__":
    asyncio.run(main())
