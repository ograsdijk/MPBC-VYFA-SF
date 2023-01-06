# MPBC-VYFA-SF
 Python interface for a MPB Communications VYFA-SF Series amplifier

# Methods and attributes of the `MPBAmplifier` class

* `enable_laser()`  
  start laser emission
* `disable_laser()`
  disable laser emission
* `get_faults()`  
  get all faults of the amplifier
* `get_alarms()`  
  get all alarms of the amplifier
* `enter_test_environment()`  
  enter the test environment of the amplifier, required to change the SHG temperature setpoint
* `save_all()`  
  save settings to non-volatile memory
* `model`  
  amplifier model
* `serial`  
  serial number
* `enabled`  
  boolean for laser emision status
* `state`
* `laser_state`  
  Current state of the laser; e.g. `BOOSTER_ON`, `OFF` etc. see `enums.py` for more.
* `mode`
* `seed_current`  
  mA
* `preamp_current`  
  mA
* `booster_current`  
  mA
* `booster_current_setpoint`  
  get and set the booster current setpoint
* `shg_temperature`  
  C
* `shg_temperature setpoint`  
  get and set the shg temperature setpoint in C
* `seed_power`  
  mW
* `output_power`  
  mW
* `output_power_setpoint`  
  if `power_stabilization` is enabled (set to `True`) this gets and sets the output power setpoint in mW
* `power_stabilization`  
  enable or disable (`True` or `False`) the output power stabilization. Only settable when emission is disabled.

# Example
```Python
from mpbc_vyfa_sf import MPBAmplifier

amp = MPBAmplifier(com_port = "COM4")

# get the current laser state
amp.laser_state

# get the seed power
amp.seed_power

# enable the laser
amp.enable_laser()

# get the output power
amp.output_power

# disable the laser
amp.disable_laser()
```