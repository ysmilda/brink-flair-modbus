"""Tests for the device-type → model mapping helpers."""

from __future__ import annotations

from brink_flair_modbus import (
    DEFAULT_FLOW_LIMITS,
    flow_limits_for,
    is_known_device_type,
    model_for_device_type,
    model_name_for_device_type,
)


def test_model_for_known_device_type() -> None:
    assert model_for_device_type(24) == 300


def test_model_name_for_known_device_type() -> None:
    assert model_name_for_device_type(24) == "Brink Flair 300"


def test_model_for_unmapped_device_type_falls_back() -> None:
    assert model_for_device_type(321) == 200


def test_model_for_unread_device_type_is_none() -> None:
    assert model_for_device_type(None) is None


def test_model_name_falls_back_to_default() -> None:
    assert model_name_for_device_type(321) == "Brink Flair 200"


def test_model_name_of_unread_device_type() -> None:
    assert model_name_for_device_type(None) == "Brink Flair"


def test_is_known_device_type() -> None:
    assert is_known_device_type(24)
    assert not is_known_device_type(321)
    assert not is_known_device_type(None)


def test_flow_limits_for_known_device_type() -> None:
    assert flow_limits_for(24) == DEFAULT_FLOW_LIMITS
