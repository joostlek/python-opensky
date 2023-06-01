"""Tests for the OpenSky Library."""
import pytest
from _pytest.python_api import approx

from python_opensky import (
    BoundingBox,
    OpenSky,
)

PRECISION = 0.01


@pytest.mark.parametrize(
    ("latitude", "longitude", "radius", "bounding_box"),
    [
        (
            0.0,
            0.0,
            111120,
            BoundingBox(
                min_latitude=-1.0,
                max_latitude=1.0,
                min_longitude=-1.0,
                max_longitude=1.0,
            ),
        ),
        (
            360.0,
            0.0,
            111120,
            BoundingBox(
                min_latitude=-1.0,
                max_latitude=1.0,
                min_longitude=-1.0,
                max_longitude=1.0,
            ),
        ),
        (
            0.0,
            45.0,
            111120,
            BoundingBox(
                min_latitude=-1.0,
                max_latitude=1.0,
                min_longitude=44.0,
                max_longitude=46.0,
            ),
        ),
        (
            0.0,
            90.0,
            111120,
            BoundingBox(
                min_latitude=-1.0,
                max_latitude=1.0,
                min_longitude=89.0,
                max_longitude=91.0,
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
        bounding_box.max_longitude,
        PRECISION,
    )


async def test_calculating_direction() -> None:
    """Test calculating direction."""
    second_point = OpenSky.calculate_point(0.0, 0.0, 25000.0, -180)
    assert second_point == (-0.22609235747829648, 2.7503115231199028e-17)
    second_point = OpenSky.calculate_point(0.0, 0.0, 25000.0, 361)
    assert second_point == (0.22605792234324162, 0.003919461063277522)
