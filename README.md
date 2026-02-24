# hass-powerpanel
Retrieve CyberPower UPS data from PowerPanel!


# Installation (Home Assistant)
_Add.._\
You should be able to add this repo to HASC.\
From there, add a new integration from the Devices and Integrations page for "PowerPanel".\
The config flow is broken, but...
- The first input is the PowerPanel host IP,
- second is the SNMP port (`161` is the default),
- `Username` is the SNMP community/service name,
- and the last input is the polling frequency (defaults to updating every `10` seconds). Maybe 30 would work best.

# Setup (PowerPanel)
_Add.._\
In short, enable SNMPv1, add/enable a community name. Give it a unique name for HASIO, and optionally set the IP to your HASIO instance.\
You may need to allow the SNMP port in your OS's firewall (UDP).


# Sensors
I attempted to disable a bunch by default, but it seems that didn't work! First time writing a component, what can I say.

| id | description | value(s) | OID |
| -- | ----------- | -------- | --- |
| `model` | Your UPS device model | `str` | `1.3.6.1.4.1.3808.1.1.1.1.1.1.0` |
| `name` | Your UPS friendly name in PowerPanel | `str` | `1.3.6.1.4.1.3808.1.1.1.1.1.2.0` |
| `power_rating` | UPS power rating (VA) | `int` | `1.3.6.1.4.1.3808.1.1.1.1.2.6.0` |
| `current_rating` | UPS current rating (A) | `int` | `1.3.6.1.4.1.3808.1.1.1.1.2.7.0` |
| -- | -- | -- | -- |
| `battery_status` | UPS battery status | [BatteryStatus](#BatteryStatus) | `1.3.6.1.4.1.3808.1.1.1.2.1.1.0` |
| `battery_time_on_battery` | Time on battery backup | `int` | `1.3.6.1.4.1.3808.1.1.1.2.1.2.0` |
| `battery_percentage` | Battery percentage | `int` | `1.3.6.1.4.1.3808.1.1.1.2.2.1.0` |
| `battery_runtime` | Remaining battery runtime | `int` | `1.3.6.1.4.1.3808.1.1.1.2.2.4.0` |
| `battery_replace_indicator` | Battery replacement indicator | [BatteryReplaceIndicator](#BatteryReplaceIndicator) | `1.3.6.1.4.1.3808.1.1.1.2.2.5.0` |
| -- | -- | -- | -- |
| `input_voltage` | Utility input voltage | `int` | `1.3.6.1.4.1.3808.1.1.1.3.2.1.0` |
| `input_frequency` | Utility input frequency | `int` | `1.3.6.1.4.1.3808.1.1.1.3.2.4.0` |
| `input_line_fail_cause` | Utility input failure reason | [InputLineFailCause](#InputLineFailCause) | `1.3.6.1.4.1.3808.1.1.1.3.2.5.0` |
| `input_status` | Utility input status | [InputStatus](#InputStatus) | `1.3.6.1.4.1.3808.1.1.1.3.2.6.0` |
| -- | -- | -- | -- |
| `output_status` | Output status | [OutputStatus](#OutputStatus) | `1.3.6.1.4.1.3808.1.1.1.4.1.1.0` |
| `output_voltage` | Output voltage | `int` | `1.3.6.1.4.1.3808.1.1.1.4.2.1.0` |
| `output_frequency` | Output frequency | `int` | `1.3.6.1.4.1.3808.1.1.1.4.2.2.0` |
| `output_load` | Output load | `int` | `1.3.6.1.4.1.3808.1.1.1.4.2.3.0` |
| `output_current` | Output current | `int` | `1.3.6.1.4.1.3808.1.1.1.4.2.4.0` |
| `output_power` | Output wattage | `int` | `NONE` (calculated by output voltage*current) |
| -- | -- | -- | -- |
| `alarm_audio` | Alarm status. (This will become an input later, as it is configurable). | `int` | `1.3.6.1.4.1.3808.1.1.1.5.2.4.0` |



# Enums
These are defined by the MIB/whatever PowerPanel throws out. I've simply read the MIB file.\
All values start a 1 and increment up by 1 each line. So, `Unknown` for example is `1`.


## BatteryStatus
_The UPS battery status, whether it's within the "low battery" threshold as determined by your required shutdown time in PowerPanel._\
`Unknown`: Unknown (batteries disconnected?)\
`BatteryNormal`: Not critically low, able to provide power.\
`BatteryLow`: Battery low and will be exhausted soon under the current load. Defined by the low battery runtime setting.


## BatteryReplaceIndicator
_Value indicates whether the UPS batteries need to be replaced (as determined by PowerPanel)._\
`NoBatteryNeedsReplacing`: Battery does not need to be replaced.\
`BatteryNeedsReplacing`: Battery needs to be replace. Replace your UPS battery as soon as possible.


## LineFailCause
_Recommended to use `InputStatus` for a more detailed reason on the utility failure, but this includes the `SelfTest` reason!_\
`NoTransfer`: No transfer, on utility power.\
`HighLineVoltage`: Input voltage over high transfer voltage.\
`LowLineVoltage`: Input voltage under low transfer voltage (including no input).\
`SelfTest`: UPS was commanded to do a self test.


## InputStatus
_Anything other than `Normal` is going to kick the UPS into running off battery._\
`Normal`: Normal utility power.\
`OverVoltage`: Input voltage over high transfer voltage.\
`UnderVoltage` Input voltage under low transfer voltage.\
`FrequencyFailure` Invalid input frequency.\
`Blackout`: No utility power.


## OutputStatus
_Note: I can only guess for 2 of these. Use something like InputStatus_\
`Unknown`: Unknown (device connectivity lost?)\
`OnLine`: Running off utility power.\
`OnBattery`: Running off battery.\
`OnBoost`: No idea.\
`OnSleep`: No idea.\
`Off`: Not running.\
`Rebooting`: Rebooting?