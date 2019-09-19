import RPi.GPIO as GPIO
from numpy.random import rand
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
