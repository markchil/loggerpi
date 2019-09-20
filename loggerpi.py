from time import sleep
from datetime import datetime
from socket import gethostname
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
from w1thermsensor import W1ThermSensor
import pickle as pkl
import lightshow

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
PWM_FREQUENCY = 60
MAX_POSITIVE_SLOPE = 10
MIN_NEGATIVE_SLOPE = -10

lightshow.setup_LED_pins()
red_pwm = lightshow.start_PWM(lightshow.RED_LED_PIN, PWM_FREQUENCY, 0)
blue_pwm = lightshow.start_PWM(lightshow.BLUE_LED_PIN, PWM_FREQUENCY, 0)

sensor = W1ThermSensor()
temperature_buffer = np.nan * np.zeros(BUFFER_LENGTH)
time_grid = np.nan * np.zeros(BUFFER_LENGTH)
figure, axes = plt.subplots()
axes.set_xlabel('Time')
axes.set_ylabel('Temperature [°F]')
axes.set_title(HOSTNAME)
temperature_line, = axes.plot_date(time_grid, temperature_buffer, '.--')
trend_line, = axes.plot_date([np.nan, np.nan], [np.nan, np.nan], '-')


def update_buffer(buffer_, new_value):
    buffer_[0:-1] = buffer_[1:]
    buffer_[-1] = new_value


def compute_trend(time_grid, temperature_buffer):
    mask = (
        (time_grid >= time_grid[-1] - SLOPE_WINDOW_DAYS) &
        (~np.isnan(temperature_buffer))
    )
    polynomial_coeffs = np.polyfit(
        time_grid[mask], temperature_buffer[mask], 1
    )
    return polynomial_coeffs


def evaluate_trend_line(time_grid, polynomial_coeffs):
    current_time = time_grid[-1]
    window_start_time = max(
        np.nanmin(time_grid), time_grid[-1] - SLOPE_WINDOW_DAYS
    )
    time_values = [window_start_time, current_time]
    temperature_values = np.polyval(polynomial_coeffs, time_values)
    return time_values, temperature_values


def update_trend_line_and_title(time_grid, polynomial_coeffs):
    time_values, temperature_values = evaluate_trend_line(
        time_grid, polynomial_coeffs
    )
    trend_line.set_xdata(time_values)
    trend_line.set_ydata(temperature_values)
    slope_F_per_hr = polynomial_coeffs[0] * 24.0
    slope_window_hr = (time_values[1] - time_values[0]) * 24.0
    axes.set_title(
        '{hostname:s}: '
        '$dT/dt={slope:.1f}$°F/hr ({window:.1f}hr window)'.format(
            hostname=HOSTNAME, slope=slope_F_per_hr, window=slope_window_hr
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
while True:
    temperature = sensor.get_temperature(UNITS)
    timestamp = date2num(datetime.now())
    print("The current temperature is {:.1f}°F".format(temperature))
    update_buffer(temperature_buffer, temperature)
    update_buffer(time_grid, timestamp)
    if steps % PLOT_UPDATE_STEP_INTERVAL_STEPS == 0:
        print("Updating plot...")
        polynomial_coeffs = compute_trend(time_grid, temperature_buffer)
        update_pwm(polynomial_coeffs[0])
        update_trend_line_and_title(time_grid, polynomial_coeffs)
        update_temperature_trace(time_grid, temperature_buffer)
        redraw_and_save_plot()
        write_data_file(time_grid, temperature_buffer)
    steps += 1
    sleep(UPDATE_INTERVAL_SECONDS)
