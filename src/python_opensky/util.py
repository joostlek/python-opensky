"""Asynchronous Python client for OpenSky."""

from __future__ import annotations

from typing import Any

from .const import LOGGER


def to_enum[EnumT](
    enum_class: type[EnumT],
    value: Any,
    default_value: EnumT,
) -> EnumT:
    """Convert a value to an enum and log if it doesn't exist."""
    try:
        return enum_class(value)  # type: ignore[call-arg]
    except ValueError:
        LOGGER.warning(
            "%s is an unsupported value for %s, please report this at https://github.com/joostlek/python-opensky/issues",
            value,
            str(enum_class),
        )
        return default_value
