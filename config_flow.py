"""Home assistant config_flow - Porssisahko.net API price data"""
from homeassistant import config_entries
from homeassistant.core import callback
from voluptuous import Coerce, Required, Schema
from .const import DOMAIN

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
  """Makes sure the transfer fee component is properly recorded"""
  VERSION = 1

  async def async_step_user(self, user_input=None):
    if self._async_current_entries():
      return self.async_abort(reason="single_instance_allowed")
    if user_input is None:
      return self.async_show_form(step_id="user", data_schema=Schema({Required("transfer_fee", default=0): Coerce(float)}))
    return self.async_create_entry(title="Porssisahko Price", data=user_input)

  @staticmethod
  @callback
  def async_get_options_flow(config_entry):
    return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
  """Presents user a dialog to set the transfer fee component"""

  def __init__(self, config_entry):
    self.config_entry = config_entry

  async def async_step_init(self, user_input=None):
    if user_input is None:
      return self.async_show_form(step_id="init", data_schema=Schema({Required("transfer_fee", default=self.config_entry.options.get("transfer_fee", 0)): Coerce(float)}))
    return self.async_create_entry(title="", data=user_input)
