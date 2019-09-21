#!/usr/bin/python3

from time import sleep
from datetime import datetime
from socket import gethostname
import numpy as np
from scipy.interpolate import UnivariateSpline
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
import pickle as pkl
try:
    import lightshow
    from w1thermsensor import W1ThermSensor
    from RPi.GPIO import cleanup
    on_pi = True
except ImportError:
    on_pi = False

if on_pi:
    UNITS = W1ThermSensor.DEGREES_F

UPDATE_INTERVAL_SECONDS = 2.0
PLOT_UPDATE_INTERVAL_STEPS = 10

TREND_WINDOW_SECONDS = 60.0 * 60.0
TREND_WINDOW_LENGTH = int(
    np.ceil(TREND_WINDOW_SECONDS / UPDATE_INTERVAL_SECONDS)
)

BUFFER_DURATION_SECONDS = 60.0 * 60.0 * 24.0
BUFFER_LENGTH = int(np.ceil(BUFFER_DURATION_SECONDS / UPDATE_INTERVAL_SECONDS))

HOSTNAME = gethostname()
PLOT_FILE_NAME = 'temperature.png'
DATA_FILE_NAME = 'temperature.pkl'

PWM_FREQUENCY_HZ = 60
MAX_SLOPE_F_PER_HR = 2
MIN_SLOPE_F_PER_HR = 0.3

SMOOTHING_PARAMETER = 500


class PlotHandler(object):
    def __init__(
        self,
        data_handler,
        filename=PLOT_FILE_NAME,
        hostname=HOSTNAME
    ):
        self.data_handler = data_handler
        self.filename = filename
        self.hostname = hostname
        self.figure, self.axes = plt.subplots()
        self.axes.set_xlabel('Time')
        self.axes.set_ylabel('Temperature [°F]')
        self.axes.set_title(self.hostname)
        self.temperature_line, = self.axes.plot_date(
            self.data_handler.time_buffer,
            self.data_handler.temperature_buffer,
            '.-',
            linewidth=1
        )
        trend_line, = self.axes.plot_date(
            self.data_handler.trend_time_buffer,
            self.data_handler.trend_temperature_buffer,
            '-'
        )

    def update_plot(self):
        self.update_trend_line()
        self.update_title()
        self.update_temperature_trace()
        self.redraw_plot()
        self.save_plot()

    @staticmethod
    def update_line(line, x_data, y_data):
        line.set_xdata(x_data)
        line.set_ydata(y_data)

    def update_trend_line(self):
        self.update_line(
            self.trend_line,
            self.data_handler.trend_time_grid,
            self.data_handler.trend_temperature_buffer
        )

    def update_temperature_trace(self):
        self.update_line(
            self.temperature_line,
            self.data_handler.time_buffer,
            self.data_handler.temperature_buffer
        )

    def update_title(self):
        self.axes.set_title(
            '{hostname:s}: '
            '$T={temperature:.1f}$°F, $dT/dt={slope:+.1f}$°F/hr'.format(
                hostname=self.hostname,
                temperature=self.data_handler.temperature_buffer[-1],
                slope=self.data_handler.slope_f_per_hr
            )
        )

    def redraw_plot(self):
        self.axes.relim()
        self.axes.autoscale_view()
        self.figure.autofmt_xdate()
        self.figure.canvas.draw_idle()

    def save_plot(self):
        self.figure.savefig(self.filename, bbox_inches='tight')


class DataHandler(object):
    def __init__(
        self,
        data_file_name=DATA_FILE_NAME,
        temperature_length=BUFFER_LENGTH,
        trend_length=TREND_WINDOW_LENGTH,
        smoothing_parameter=SMOOTHING_PARAMETER
    ):
        self.data_file_name = data_file_name
        self.temperature_length = temperature_length
        self.trend_length = trend_length
        self.smoothing_parameter = smoothing_parameter
        try:
            with open(self.data_file_name, 'rb') as pf:
                self.time_buffer, self.temperature_buffer = pkl.load(pf)
        except FileNotFoundError:
            self.temperature_buffer = np.nan * np.zeros(
                self.temperature_length
            )
            self.time_buffer = np.nan * np.zeros(self.temperature_length)
        self.trend_temperature_buffer = np.nan * np.zeros(self.trend_length)
        self.trend_time_buffer = np.nan * np.zeros(self.trend_length)

    @staticmethod
    def update_buffer(buffer_, new_value):
        buffer_[0:-1] = buffer_[1:]
        buffer_[-1] = new_value

    def record_measurement(self, timestamp, temperature):
        self.update_buffer(self.time_buffer, timestamp)
        self.update_buffer(self.temperature_buffer, temperature)

    def trend_grid(self, array):
        array = array[-self.trend_length:]
        array = array[~np.isnan(array)]
        return array

    @property
    def trend_time_grid(self):
        return self.trend_grid(self.time_grid)

    @property
    def trend_temperature_grid(self):
        return self.trend_grid(self.temperature_grid)

    def update_trend(self):
        time_grid = self.trend_time_grid
        self.spline = UnivariateSpline(
            time_grid,
            self.trend_temperature_grid,
            s=self.smoothing_parameter
        )
        self.trend_time_buffer = time_grid
        self.trend_temperature_buffer = self.spline(time_grid)
        self.slope_f_per_hr = self.spline(time_grid[-1], 1) / 24.0

        return self.slope_f_per_hr

    def write_data_file(self):
        with open(self.data_file_name, 'wb') as pf:
            pkl.dump([self.time_buffer, self.temperature_buffer], pf)


class LightHandler(object):
    def __init__(
        self,
        pwm_frequency_hz=PWM_FREQUENCY_HZ,
        min_slope_f_per_hr=MIN_SLOPE_F_PER_HR,
        max_slope_f_per_hr=MAX_SLOPE_F_PER_HR
    ):
        self.pwm_frequency_hz = pwm_frequency_hz
        self.min_slope_f_per_hr = min_slope_f_per_hr
        self.max_slope_f_per_hr = max_slope_f_per_hr

        try:
            lightshow.setup_LED_pins()
            self.red_pwm = lightshow.start_PWM(
                lightshow.RED_LED_PIN, self.pwm_frequency_hz, 0
            )
            self.blue_pwm = lightshow.start_PWM(
                lightshow.BLUE_LED_PIN, self.pwm_frequency_hz, 0
            )
        except NameError:
            pass

    def slope_to_duty_cycle(self, slope_f_per_hr):
        return 100 * (
            min(
                max(0, (abs(slope_f_per_hr) - self.min_slope_f_per_hr)),
                self.max_slope_f_per_hr - self.min_slope_f_per_hr
            ) / (self.max_slope_f_per_hr - self.min_slope_f_per_hr)
        )

    def update_pwm(self, slope_f_per_hr):
        duty_cycle = self.slope_to_duty_cycle(slope_f_per_hr)
        if slope_f_per_hr > 0:
            self.red_pwm.ChangeDutyCycle(duty_cycle)
            self.blue_pwm.ChangeDutyCycle(0)
        else:
            self.red_pwm.ChangeDutyCycle(0)
            self.blue_pwm.ChangeDutyCycle(duty_cycle)


if __name__ == '__main__':
    if not on_pi:
        raise RuntimeError('GPIO is not available!')

    sensor = W1ThermSensor()
    light_handler = LightHandler()
    data_handler = DataHandler()
    plot_handler = PlotHandler(data_handler)

    steps = 1
    try:
        while True:
            temperature = sensor.get_temperature(UNITS)
            timestamp = date2num(datetime.now())
            data_handler.record_measurement(timestamp, temperature)
            if steps % PLOT_UPDATE_INTERVAL_STEPS == 0:
                slope_f_per_hr = data_handler.update_trend()
                plot_handler.update_plot()
                light_handler.update_pwm(slope_f_per_hr)
                data_handler.write_data_file()
                steps = 0
            steps += 1
            sleep(UPDATE_INTERVAL_SECONDS)
    finally:
        cleanup()
