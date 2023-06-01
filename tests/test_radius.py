"""Tests for the OpenSky Library."""
import pytest
from _pytest.python_api import approx

from python_opensky import (
    BoundingBox,
    OpenSky,
)


@pytest.mark.parametrize(
    ("latitude", "longitude", "radius", "bounding_box"),
    [
        (
            0.0,
            0.0,
            25000,
            BoundingBox(
                -0.22609235747829648,
                0.22609235747829648,
                -0.22457882102988042,
                0.22457882102988042,
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
    assert res_bounding_box.min_latitude == approx(bounding_box.min_latitude, 0.000001)
    assert res_bounding_box.max_latitude == approx(bounding_box.max_latitude, 0.000001)
    assert res_bounding_box.min_longitude == approx(
        bounding_box.min_longitude,
        0.000001,
    )
    assert res_bounding_box.max_longitude == approx(
        bounding_box.min_longitude,
        0.000001,
    )
