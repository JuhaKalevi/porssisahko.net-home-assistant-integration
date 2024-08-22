"""The Porssisahko Price integration."""
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import Platform
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
  """Set up Porssisahko Price from a config entry."""
  _LOGGER.debug("Setting up Porssisahko Price integration for entry: %s", entry.entry_id)
  hass.data.setdefault(DOMAIN, {})
  try:
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
  except Exception as ex:
    _LOGGER.error("Error setting up platform: %s", ex)
    raise ConfigEntryNotReady from ex
  entry.async_on_unload(entry.add_update_listener(options_update_listener))
  hass.data[DOMAIN][entry.entry_id] = True
  _LOGGER.debug("Porssisahko Price integration setup completed for entry: %s", entry.entry_id)
  return True

async def options_update_listener(hass: HomeAssistant, entry: ConfigEntry):
  _LOGGER.debug("Handling options update for entry: %s", entry.entry_id)
  await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
  _LOGGER.debug("Unloading Porssisahko Price integration for entry: %s", entry.entry_id)
  if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
    hass.data[DOMAIN].pop(entry.entry_id)
  return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
  await async_unload_entry(hass, entry)
  await async_setup_entry(hass, entry)
