# Python: OpenSky

[![GitHub Release][releases-shield]][releases]
[![Python Versions][python-versions-shield]][pypi]
![Project Stage][project-stage-shield]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE.md)

[![Build Status][build-shield]][build]
[![Code Coverage][codecov-shield]][codecov]
[![Code Smells][code-smells]][sonarcloud]

Asynchronous Python client for the OpenSky API.

## About

This package allows you to request data about aircraft around the world.

## Installation

```bash
pip install python-opensky
```

## Usage

```python
import asyncio

from python_opensky import OpenSky, StatesResponse


async def main() -> None:
    """Show example of fetching all flight states."""
    async with OpenSky() as opensky:
        states: StatesResponse = await opensky.get_states()
        print(states)


if __name__ == "__main__":
    asyncio.run(main())
```

## Changelog & Releases

This repository keeps a change log using [GitHub's releases][releases]
functionality. The format of the log is based on
[Keep a Changelog][keepchangelog].

Releases are based on [Semantic Versioning][semver], and use the format
of ``MAJOR.MINOR.PATCH``. In a nutshell, the version will be incremented
based on the following:

- ``MAJOR``: Incompatible or major changes.
- ``MINOR``: Backwards-compatible new features and enhancements.
- ``PATCH``: Backwards-compatible bugfixes and package updates.

## Contributing

This is an active open-source project. We are always open to people who want to
use the code or contribute to it.

We've set up a separate document for our
[contribution guidelines](.github/CONTRIBUTING.md).

Thank you for being involved! :heart_eyes:

## Setting up development environment

This Python project is fully managed using the [Poetry][poetry] dependency manager. But also relies on the use of NodeJS for certain checks during development.

You need at least:

- Python 3.10+
- [Poetry][poetry-install]
- NodeJS 12+ (including NPM)

To install all packages, including all development requirements:

```bash
npm install
poetry install
```

As this repository uses the [pre-commit][pre-commit] framework, all changes
are linted and tested with each commit. You can run all checks and tests
manually, using the following command:

```bash
poetry run pre-commit run --all-files
```

To run just the Python tests:

```bash
poetry run pytest
```

## Authors & contributors

The original setup of this repository is heavily inspired by [Franck Nijhof][frenck].

The content is by [Joost Lekkerkerker][joostlek]

For a full list of all authors and contributors,
check [the contributor's page][contributors].

## License

MIT License

Copyright (c) 2023 Joost Lekkerkerker

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[build-shield]: https://github.com/joostlek/python-opensky/actions/workflows/tests.yaml/badge.svg
[build]: https://github.com/joostlek/python-opensky/actions
[code-smells]: https://sonarcloud.io/api/project_badges/measure?project=joostlek_python-opensky&metric=code_smells
[codecov-shield]: https://codecov.io/gh/joostlek/python-opensky/branch/master/graph/badge.svg
[codecov]: https://codecov.io/gh/joostlek/python-opensky
[commits-shield]: https://img.shields.io/github/commit-activity/y/joostlek/python-opensky.svg
[commits]: https://github.com/joostlek/python-opensky/commits/master
[contributors]: https://github.com/joostlek/python-opensky/graphs/contributors
[frenck]: https://github.com/frenck
[joostlek]: https://github.com/joostlek
[keepchangelog]: http://keepachangelog.com/en/1.0.0/
[license-shield]: https://img.shields.io/github/license/joostlek/python-opensky.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2023.svg
[poetry-install]: https://python-poetry.org/docs/#installation
[poetry]: https://python-poetry.org
[pre-commit]: https://pre-commit.com/
[project-stage-shield]: https://img.shields.io/badge/project%20stage-stable-green.svg
[python-versions-shield]: https://img.shields.io/pypi/pyversions/python-opensky
[releases-shield]: https://img.shields.io/github/release/joostlek/python-opensky.svg
[releases]: https://github.com/joostlek/python-opensky/releases
[semver]: http://semver.org/spec/v2.0.0.html
[sonarcloud]: https://sonarcloud.io/summary/new_code?id=joostlek_python-opensky
[pypi]: https://pypi.org/project/python-opensky/
