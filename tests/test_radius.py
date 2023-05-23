"""Tests for the OpenSky Library."""


from python_opensky import (
    OpenSky,
)


async def test_calculating_bounding_box() -> None:
    """Test calculating bounding box."""
    bounding_box = OpenSky.get_bounding_box(0.0, 0.0, 25000)
    assert bounding_box.min_latitude == -0.22609235747829648
    assert bounding_box.max_latitude == 0.22609235747829648
    assert bounding_box.min_longitude == -0.22457882102988042
    assert bounding_box.max_longitude == 0.22457882102988042


async def test_calculating_direction() -> None:
    """Test calculating direction."""
    second_point = OpenSky.calculate_point(0.0, 0.0, 25000.0, -180)
    assert second_point == (-0.22609235747829648, 2.7503115231199028e-17)
    second_point = OpenSky.calculate_point(0.0, 0.0, 25000.0, 361)
    assert second_point == (0.22605792234324162, 0.003919461063277522)
