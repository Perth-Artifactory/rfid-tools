import time
import RPi.GPIO as GPIO
import os
GPIO.setmode(GPIO.BCM)
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(21, GPIO.OUT) # Relay 1

import serial
serial = serial.Serial("/dev/ttyAMA0", baudrate=9600)

code = ''

while True:
       data = serial.read()
       input_state = GPIO.input(13)
       if data == '\r':
               os.system ("aplay /opt/sounds/granted.wav")
               os.system ("mpg123 /opt/sounds/cat.mp3")
               GPIO.output(21, True)
               print(code)
               code = ''
               time.sleep(3)
               GPIO.output(21, False)
       if input_state == False:
               os.system ("mpg123 /opt/sounds/cat.mp3")
       else:
               code = code + data

