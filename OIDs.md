# sensors
model	OID	 .1.3.6.1.4.1.3808.1.1.1.1.1.1.0
name	OID	 .1.3.6.1.4.1.3808.1.1.1.1.1.2.0
firmwareVersion OID	.1.3.6.1.4.1.3808.1.1.1.1.2.1.0
serialNumber OID	.1.3.6.1.4.1.3808.1.1.1.1.2.3.0
powerpanelVersion OID	.1.3.6.1.4.1.3808.1.1.1.1.2.4.0


powerRating (max output W)	OID	 .1.3.6.1.4.1.3808.1.1.1.1.2.6.0
currentRating (max output W)	OID	 .1.3.6.1.4.1.3808.1.1.1.1.2.7.0

batteryStatus (normal|low)	OID	 .1.3.6.1.4.1.3808.1.1.1.2.1.1.0
timeOnBattery (timeticks on battery)	OID	 .1.3.6.1.4.1.3808.1.1.1.2.1.2.0
batteryPercentage	OID	 .1.3.6.1.4.1.3808.1.1.1.2.2.1.0
batteryRuntimeRemaining	OID	 .1.3.6.1.4.1.3808.1.1.1.2.2.4.0
batteryReplaceIndicator	OID	 .1.3.6.1.4.1.3808.1.1.1.2.2.5.0

inputVoltage	OID	 .1.3.6.1.4.1.3808.1.1.1.3.2.1.0
inputFrequency	OID	 .1.3.6.1.4.1.3808.1.1.1.3.2.4.0
inputLineFailCause (noTransfer, highLineVoltage, brownout, selfTest)	OID	 .1.3.6.1.4.1.3808.1.1.1.3.2.5.0
inputStatus (normal, overVoltage, underVoltage, frequencyFailure, blackout)	OID	 .1.3.6.1.4.1.3808.1.1.1.3.2.6.0

outputStatus (unknown, onLine, onBattery, onBoost, onSleep, off, rebooting)	OID	 .1.3.6.1.4.1.3808.1.1.1.3.2.6.0
outputVoltage	OID	 .1.3.6.1.4.1.3808.1.1.1.4.2.1.0
outputFrequency	OID	 .1.3.6.1.4.1.3808.1.1.1.4.2.2.0
outputLoad (xx%)	OID	 .1.3.6.1.4.1.3808.1.1.1.4.2.3.0
outputCurrent (amps)	OID	 .1.3.6.1.4.1.3808.1.1.1.4.2.4.0
outputPower (manual, do current\*voltage -> watts)



# inputs?
alarmAudio (timed, enable, disable, mute)	OID	 .1.3.6.1.4.1.3808.1.1.1.5.2.4.0