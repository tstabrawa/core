"""Test Scrape component setup process."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest

from homeassistant.components.scrape.const import DOMAIN
from homeassistant.components.scrape.sensor import SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from . import MockRestData, return_integration_config

from tests.common import async_fire_time_changed


async def test_setup_config(hass: HomeAssistant) -> None:
    """Test setup from yaml."""
    config = {
        DOMAIN: [
            return_integration_config(
                sensors=[{"select": ".current-version h1", "name": "HA version"}]
            )
        ]
    }

    mocker = MockRestData("test_scrape_sensor")
    with patch(
        "homeassistant.components.rest.RestData",
        return_value=mocker,
    ) as mock_setup:
        assert await async_setup_component(hass, DOMAIN, config)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.ha_version")
    assert state.state == "Current Version: 2021.12.10"

    assert len(mock_setup.mock_calls) == 1


async def test_setup_no_data_fails_with_recovery(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test setup entry no data fails and recovers."""
    config = {
        DOMAIN: [
            return_integration_config(
                sensors=[{"select": ".current-version h1", "name": "HA version"}]
            ),
        ]
    }

    mocker = MockRestData("test_scrape_sensor_no_data")
    with patch(
        "homeassistant.components.rest.RestData",
        return_value=mocker,
    ):
        assert await async_setup_component(hass, DOMAIN, config)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.ha_version")
        assert state is None

        assert "Platform scrape not ready yet" in caplog.text

        mocker.payload = "test_scrape_sensor"
        async_fire_time_changed(hass, datetime.utcnow() + SCAN_INTERVAL)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.ha_version")
    assert state.state == "Current Version: 2021.12.10"


async def test_setup_config_no_configuration(hass: HomeAssistant) -> None:
    """Test setup from yaml missing configuration options."""
    config = {DOMAIN: None}

    assert await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()

    entities = er.async_get(hass)
    assert entities.entities == {}


async def test_setup_config_no_sensors(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test setup from yaml with no configured sensors finalize properly."""
    config = {
        DOMAIN: [
            {
                "resource": "https://www.address.com",
                "verify_ssl": True,
            },
            {
                "resource": "https://www.address2.com",
                "verify_ssl": True,
                "sensor": None,
            },
        ]
    }

    mocker = MockRestData("test_scrape_sensor")
    with patch(
        "homeassistant.components.rest.RestData",
        return_value=mocker,
    ):
        assert await async_setup_component(hass, DOMAIN, config)
        await hass.async_block_till_done()
