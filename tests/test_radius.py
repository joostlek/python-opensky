"""Tests for the OpenSky Library."""
import pytest
from _pytest.python_api import approx

from python_opensky import (
    BoundingBox,
    OpenSky,
)

PRECISION = 0.001

@pytest.mark.parametrize(
    ("latitude", "longitude", "radius", "bounding_box"),
    [
        (
            0.0,
            0.0,
            111120,
            BoundingBox(
                min_latitude=-0.9993261684968934,
                max_latitude=0.9993261684968934,
                min_longitude=-0.9993261684968934,
                max_longitude=0.9993261684968934,
            ),
        ),
    ],
)
async def test_calculating_bounding_box(
    latitude: float,
    longitude: float,
    radius: float,
    bounding_box: BoundingBox,
) -> None:
    """Test calculating bounding box."""
    res_bounding_box = OpenSky.get_bounding_box(latitude, longitude, radius)
    assert res_bounding_box.min_latitude == approx(bounding_box.min_latitude, PRECISION)
    assert res_bounding_box.max_latitude == approx(bounding_box.max_latitude, PRECISION)
    assert res_bounding_box.min_longitude == approx(
        bounding_box.min_longitude,
        PRECISION,
    )
    assert res_bounding_box.max_longitude == approx(
        bounding_box.min_longitude,
        PRECISION,
    )
