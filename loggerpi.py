#!/usr/bin/python3

import matplotlib
matplotlib.use('pdf')
from time import sleep
from datetime import datetime
from socket import gethostname
import numpy as np
from scipy.interpolate import UnivariateSpline
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
from w1thermsensor import W1ThermSensor
import pickle as pkl
import lightshow
from RPi.GPIO import cleanup

UPDATE_INTERVAL_SECONDS = 2.0
PLOT_UPDATE_STEP_INTERVAL_STEPS = 10
BUFFER_DURATION_SECONDS = 60.0 * 60.0 * 24.0
BUFFER_LENGTH = int(np.ceil(BUFFER_DURATION_SECONDS / UPDATE_INTERVAL_SECONDS))
UNITS = W1ThermSensor.DEGREES_F
HOSTNAME = gethostname()
PLOT_FILE_NAME = 'temperature.png'
DATA_FILE_NAME = 'temperature.pkl'
PWM_FREQUENCY = 60
MAX_POSITIVE_SLOPE = 10
MIN_NEGATIVE_SLOPE = -10
SMOOTHING_PARAMETER = 800

lightshow.setup_LED_pins()
red_pwm = lightshow.start_PWM(lightshow.RED_LED_PIN, PWM_FREQUENCY, 0)
blue_pwm = lightshow.start_PWM(lightshow.BLUE_LED_PIN, PWM_FREQUENCY, 0)

sensor = W1ThermSensor()

try:
    with open(DATA_FILE_NAME, 'rb') as pf:
        time_grid, temperature_buffer = pkl.load(pf)
except FileNotFoundError:
    temperature_buffer = np.nan * np.zeros(BUFFER_LENGTH)
    time_grid = np.nan * np.zeros(BUFFER_LENGTH)

figure, axes = plt.subplots()
axes.set_xlabel('Time')
axes.set_ylabel('Temperature [°F]')
axes.set_title(HOSTNAME)
temperature_line, = axes.plot_date(time_grid, temperature_buffer, '.--')
trend_line, = axes.plot_date(time_grid, temperature_buffer, '-')


def update_buffer(buffer_, new_value):
    buffer_[0:-1] = buffer_[1:]
    buffer_[-1] = new_value


def compute_trend(time_grid, temperature_buffer):
    mask = ~np.isnan(temperature_buffer)
    spline = UnivariateSpline(
        time_grid[mask], temperature_buffer[mask], s=SMOOTHING_PARAMETER
    )
    return spline


def evaluate_trend(time_grid, spline):
    mask = ~np.isnan(temperature_buffer)
    time_values = time_grid[mask]
    temperature_values = spline(time_values)
    return time_values, temperature_values


def update_trend_line_and_title(time_grid, spline):
    time_values, temperature_values = evaluate_trend(time_grid, spline)
    trend_line.set_xdata(time_values)
    trend_line.set_ydata(temperature_values)
    slope_F_per_hr = spline(time_grid[-1], 1) / 24.0
    axes.set_title(
        '{hostname:s}: $dT/dt={slope:.1f}$°F/hr'.format(
            hostname=HOSTNAME, slope=slope_F_per_hr
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


def slope_to_duty_cycle(slope):
    slope /= 24.0
    if slope >= 0:
        return min(slope, MAX_POSITIVE_SLOPE) / MAX_POSITIVE_SLOPE
    else:
        return max(slope, MIN_NEGATIVE_SLOPE) / MIN_NEGATIVE_SLOPE


def update_pwm(slope):
    duty_cycle = slope_to_duty_cycle(slope)
    if slope > 0:
        red_pwm.ChangeDutyCycle(duty_cycle)
        blue_pwm.ChangeDutyCycle(0)
    else:
        red_pwm.ChangeDutyCycle(0)
        blue_pwm.ChangeDutyCycle(duty_cycle)


steps = 1
try:
    while True:
        temperature = sensor.get_temperature(UNITS)
        timestamp = date2num(datetime.now())
        update_buffer(temperature_buffer, temperature)
        update_buffer(time_grid, timestamp)
        if steps % PLOT_UPDATE_STEP_INTERVAL_STEPS == 0:
            spline = compute_trend(time_grid, temperature_buffer)
            update_pwm(spline(time_grid[-1], 1))
            update_trend_line_and_title(time_grid, spline)
            update_temperature_trace(time_grid, temperature_buffer)
            redraw_and_save_plot()
            write_data_file(time_grid, temperature_buffer)
        steps += 1
        sleep(UPDATE_INTERVAL_SECONDS)
finally:
    cleanup()
