from time import sleep
from datetime import datetime
from socket import gethostname
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
from w1thermsensor import W1ThermSensor

UPDATE_INTERVAL = 2.0
PLOT_UPDATE_STEP_INTERVAL = 10
BUFFER_DURATION = 60.0 * 60.0 * 1.0
BUFFER_LENGTH = int(np.ceil(BUFFER_DURATION / UPDATE_INTERVAL))
UNITS = W1ThermSensor.DEGREES_F
HOSTNAME = gethostname()


def update_buffer(buffer_, new_value):
    buffer_[0:-1] = buffer_[1:]
    buffer_[-1] = new_value


sensor = W1ThermSensor()
temperature_buffer = np.nan * np.zeros(BUFFER_LENGTH)
time_grid = np.nan * np.zeros(BUFFER_LENGTH)
# time_grid = np.arange(BUFFER_LENGTH) * UPDATE_INTERVAL / 60.0
# time_grid = -1 * time_grid[::-1]
figure, axes = plt.subplots()
axes.set_xlabel('Time')
axes.set_ylabel('Temperature [°F]')
axes.set_title(HOSTNAME)
line, = axes.plot_date(time_grid, temperature_buffer, '.--')

steps = 0
while True:
    temperature = sensor.get_temperature(UNITS)
    timestamp = date2num(datetime.now())
    print("The current temperature is {:.1f}°F".format(temperature))
    update_buffer(temperature_buffer, temperature)
    update_buffer(time_grid, timestamp)
    if steps % PLOT_UPDATE_STEP_INTERVAL == 0:
        print("Updating plot...")
        line.set_xdata(time_grid)
        line.set_ydata(temperature_buffer)
        axes.relim()
        axes.autoscale_view()
        figure.autofmt_xdate()
        figure.canvas.draw_idle()
        figure.savefig('temperature.png', bbox_inches='tight')
    steps += 1
    sleep(UPDATE_INTERVAL)
