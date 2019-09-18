from time import sleep
import numpy as np
import matplotlib.pyplot as plt
from w1thermsensor import W1ThermSensor

UPDATE_INTERVAL = 1.0
BUFFER_DURATION = 60.0 * 60.0 * 1.0
BUFFER_LENGTH = int(np.ceil(BUFFER_DURATION / UPDATE_INTERVAL))
UNITS = W1ThermSensor.DEGREES_F

sensor = W1ThermSensor()
temperature_buffer = np.nan * np.ones(BUFFER_LENGTH)
time_grid = np.arange(BUFFER_LENGTH) * UPDATE_INTERVAL / 60.0
time_grid = -1 * time_grid[::-1]
figure, axis = plt.subplots()
axis.set_xlabel('Time Relative to Now [min]')
axis.set_ylabel('Temperature [°F]')
line, = axis.plot(time_grid, temperature_buffer, '.--')

while True:
    temperature = sensor.get_temperature(UNITS)
    print("The current temperature is {:.1f}°F".format(temperature))
    temperature_buffer[0:-1] = temperature_buffer[1:]
    temperature_buffer[-1] = temperature
    line.set_ydata(temperature_buffer)
    figure.canvas.draw_idle()
    figure.savefig('temperature.png')
    sleep(UPDATE_INTERVAL)
