from time import sleep
from w1thermsensor import W1ThermSensor

UPDATE_INTERVAL = 1.0
UNITS = W1ThermSensor.DEGREES_F

sensor = W1ThermSensor()

while True:
    temperature = sensor.get_temperature(UNITS)
    print("The current temperature is {:.1f}°F".format(temperature))
    sleep(UPDATE_INTERVAL)
