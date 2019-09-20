from time import sleep
from datetime import datetime
from socket import gethostname
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
from w1thermsensor import W1ThermSensor
import pickle as pkl

UPDATE_INTERVAL_SECONDS = 2.0
SLOPE_WINDOW_HR = 1.0
SLOPE_WINDOW_DAYS = SLOPE_WINDOW_HR / 24.0
PLOT_UPDATE_STEP_INTERVAL_STEPS = 10
BUFFER_DURATION_SECONDS = 60.0 * 60.0 * 24.0
BUFFER_LENGTH = int(np.ceil(BUFFER_DURATION_SECONDS / UPDATE_INTERVAL_SECONDS))
UNITS = W1ThermSensor.DEGREES_F
HOSTNAME = gethostname()
PLOT_FILE_NAME = 'temperature.png'
DATA_FILE_NAME = 'temperature.pkl'


def update_buffer(buffer_, new_value):
    buffer_[0:-1] = buffer_[1:]
    buffer_[-1] = new_value


sensor = W1ThermSensor()
temperature_buffer = np.nan * np.zeros(BUFFER_LENGTH)
time_grid = np.nan * np.zeros(BUFFER_LENGTH)
figure, axes = plt.subplots()
axes.set_xlabel('Time')
axes.set_ylabel('Temperature [°F]')
axes.set_title(HOSTNAME)
temperature_line, = axes.plot_date(time_grid, temperature_buffer, '.--')
trend_line, = axes.plot_date([np.nan, np.nan], [np.nan, np.nan])


def compute_trend(time_grid, temperature_buffer):
    mask = (
        (time_grid >= time_grid[-1] - SLOPE_WINDOW_DAYS) &
        (~np.isnan(temperature_buffer))
    )
    polynomial_coeffs = np.polyfit(
        time_grid[mask], temperature_buffer[mask], 1
    )
    return polynomial_coeffs


def update_trend_line(current_time, polynomial_coeffs):
    time_values = [current_time - SLOPE_WINDOW_DAYS, current_time]
    temperature_values = np.polyval(polynomial_coeffs, time_values)
    trend_line.set_xdata(time_values)
    trend_line.set_ydata(temperature_values)
    slope_F_per_hr = polynomial_coeffs[0] * 24.0
    axes.set_title(
        '{hostname:s}: '
        '$dT/dt={slope:.1f}$°F/hr ({window:.1f}hr window)'.format(
            hostname=HOSTNAME, slope=slope_F_per_hr, window=SLOPE_WINDOW_HR
        )
    )


def update_temperature_trace(time_grid, temperature_buffer):
    temperature_line.set_xdata(time_grid)
    temperature_line.set_ydata(temperature_buffer)


def redraw_and_save_plot():
    axes.relim()
    axes.autoscale_view()
    figure.autofmt_xdate()
    figure.canvas.draw_idle()
    figure.savefig(PLOT_FILE_NAME, bbox_inches='tight')


def write_data_file(time_grid, temperature_buffer):
    with open(DATA_FILE_NAME, 'wb') as pf:
        pkl.dump([time_grid, temperature_buffer], pf)


steps = 1
while True:
    temperature = sensor.get_temperature(UNITS)
    timestamp = date2num(datetime.now())
    print("The current temperature is {:.1f}°F".format(temperature))
    update_buffer(temperature_buffer, temperature)
    update_buffer(time_grid, timestamp)
    if steps % PLOT_UPDATE_STEP_INTERVAL_STEPS == 0:
        print("Updating plot...")
        polynomial_coeffs = compute_trend(time_grid, temperature_buffer)
        update_trend_line(time_grid[-1], polynomial_coeffs)
        update_temperature_trace(time_grid, temperature_buffer)
        redraw_and_save_plot(time_grid, temperature_buffer)
        write_data_file(time_grid, temperature_buffer)
    steps += 1
    sleep(UPDATE_INTERVAL_SECONDS)
