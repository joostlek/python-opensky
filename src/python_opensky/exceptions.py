"""Asynchronous Python client for the OpenSky API."""


class OpenSkyError(Exception):
    """Generic exception."""


class OpenSkyConnectionError(OpenSkyError):
    """OpenSky connection exception."""


class OpenSkyCoordinateError(OpenSkyError):
    """OpenSky coordinate exception."""
