"""Tests for the OpenSky Library."""
from _pytest.python_api import approx

from python_opensky import (
    OpenSky,
)


async def test_calculating_bounding_box() -> None:
    """Test calculating bounding box."""
    bounding_box = OpenSky.get_bounding_box(0.0, 0.0, 25000)
    # assert bounding_box.min_latitude == approx(-0.22609235747829648, 0.000001)
    # assert bounding_box.max_latitude == approx(0.22609235747829648, 0.000001)
    assert bounding_box.min_longitude == approx(-0.22457882102988042, 0.000001)
    assert bounding_box.max_longitude == approx(0.22457882102988042, 0.000001)
