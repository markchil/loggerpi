# Copyright 2019 Mark Chilenski
# This program is distributed under the terms of the GNU General Purpose
# License (GPL).
# Refer to http://www.gnu.org/licenses/gpl.txt
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import RPi.GPIO as GPIO
from numpy.random import rand, randint
from time import sleep

BLUE_LED_PIN = 12
GREEN_LED_PIN = 13
RED_LED_PIN = 19


def setup_LED_pins():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BLUE_LED_PIN, GPIO.OUT)
    GPIO.setup(GREEN_LED_PIN, GPIO.OUT)
    GPIO.setup(RED_LED_PIN, GPIO.OUT)


def start_PWM(pin, frequency, duty_cycle):
    pwm = GPIO.PWM(pin, frequency)
    pwm.start(duty_cycle)
    return pwm


def zero_PWMs(pwms):
    for pwm in pwms:
        pwm.ChangeDutyCycle(0)


def start_RGB_PWM(frequency=60.0, duty_cycle=0.0):
    try:
        if len(duty_cycle) != 3:
            raise ValueError('Wrong number of duty cycles!')
    except TypeError:
        duty_cycle = [duty_cycle] * 3
    pwms = []
    for pin, dc in zip([RED_LED_PIN, GREEN_LED_PIN, BLUE_LED_PIN], duty_cycle):
        pwms.append(start_PWM(pin, frequency, dc))
    return pwms


def disco_mode_1(interval, pwms):
    while True:
        duty_cycles = 100 * rand(len(pwms))
        for dc, pwm in zip(duty_cycles, pwms):
            pwm.ChangeDutyCycle(dc)
        sleep(interval)


def disco_mode_2(interval, pwms):
    zero_PWMs(pwms)
    active_PWM = pwms[0]
    while True:
        active_PWM.ChangeDutyCycle(0)
        active_PWM = pwms[randint(len(pwms))]
        duty_cycle = 100 * rand(1)
        active_PWM.ChangeDutyCycle(duty_cycle)
        sleep(interval)
