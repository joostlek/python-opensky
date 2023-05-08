"""Tests for the OpenSky Library."""
import pytest

from python_opensky import BoundingBox
from python_opensky.exceptions import OpenSkyCoordinateError


def test_degrees() -> None:
    """Test if validation passes."""
    box: BoundingBox = BoundingBox(
        min_latitude=0,
        max_latitude=0,
        min_longitude=0,
        max_longitude=0,
    )
    box.validate()
    box = BoundingBox(
        min_latitude=-91,
        max_latitude=0,
        min_longitude=0,
        max_longitude=0,
    )
    with pytest.raises(OpenSkyCoordinateError):
        box.validate()
    box = BoundingBox(
        min_latitude=0,
        max_latitude=0,
        min_longitude=-181,
        max_longitude=0,
    )
    with pytest.raises(OpenSkyCoordinateError):
        box.validate()
