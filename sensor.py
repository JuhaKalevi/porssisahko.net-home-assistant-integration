"""Home Assistant sensors entity - Porssisahko.net API price data"""
from __future__ import annotations
from datetime import timedelta
import logging
import aiohttp
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.exceptions import ConfigEntryNotReady
from .const import CONF_TRANSFER_FEE

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)

class PorssisahkoApiClient:

  def __init__(self, session: aiohttp.ClientSession):
    self._session = session

  async def get_latest_prices(self):
    """API response has 48 of past, current & future price data"""
    async with self._session.get("https://api.porssisahko.net/v1/latest-prices.json") as response:
      if response.status == 200:
        data = await response.json()
        return data["prices"]
      _LOGGER.error("API request failed with status %s", response.status)

class PorssisahkoCoordinator(DataUpdateCoordinator):

  def __init__(self, hass: HomeAssistant, client: PorssisahkoApiClient, transfer_fee: float):
    super().__init__(hass, _LOGGER, name="Porssisahko Price", update_interval=SCAN_INTERVAL)
    self.client = client
    self.transfer_fee = transfer_fee
    self.data = None

  async def _async_update_data(self):
    try:
      _LOGGER.debug("Fetching latest prices from API")
      prices = await self.client.get_latest_prices()
      now = dt_util.now()
      for price_data in prices:
        start_time = dt_util.parse_datetime(price_data["startDate"])
        if start_time <= now < start_time + timedelta(hours=1):
          energy_price = price_data["price"] / 100
          total_price = energy_price + self.transfer_fee
          _LOGGER.debug("Updated price: %s (Energy: %s, Transfer: %s)", total_price, energy_price, self.transfer_fee)
          return total_price
      _LOGGER.warning("No current price found in the data")
      return None
    except Exception as err:
      _LOGGER.error("Error communicating with API: %s", err)
      raise

class PorssisahkoPriceSensor(CoordinatorEntity, SensorEntity):

  _attr_name = "Porssisahko Electricity Price"
  _attr_native_unit_of_measurement = "€/kWh"
  _attr_device_class = SensorDeviceClass.MONETARY
  _attr_state_class = SensorStateClass.TOTAL

  def __init__(self, coordinator: PorssisahkoCoordinator, entry: ConfigEntry):
    super().__init__(coordinator)
    self._attr_unique_id = f"{entry.entry_id}_current_price"
    self.entry = entry
    _LOGGER.debug("Initializing PorssisahkoPriceSensor with unique_id: %s", self._attr_unique_id)

  @property
  def native_value(self):
    return self.coordinator.data

  @property
  def extra_state_attributes(self):
    return {"transfer_fee": self.coordinator.transfer_fee}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
  _LOGGER.debug("Setting up Porssisahko Price sensor for entry: %s", entry.entry_id)
  try:
    session = async_get_clientsession(hass)
    client = PorssisahkoApiClient(session)
    transfer_fee = entry.options.get(CONF_TRANSFER_FEE, 0)
    coordinator = PorssisahkoCoordinator(hass, client, transfer_fee)
    await coordinator.async_config_entry_first_refresh()
    sensor = PorssisahkoPriceSensor(coordinator, entry)
    async_add_entities([sensor], True)
    _LOGGER.debug("Added Porssisahko Price sensor: %s", sensor.unique_id)
    return True
  except Exception as ex:
    _LOGGER.error("Error setting up Porssisahko Price sensor: %s", ex)
    raise ConfigEntryNotReady from ex
