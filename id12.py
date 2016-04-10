#!/usr/bin/env python
import time
import RPi.GPIO as GPIO
import csv
import os
import syslog
GPIO.setmode(GPIO.BCM)
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(21, GPIO.OUT) # Relay 1

import serial
serial = serial.Serial("/dev/ttyAMA0", baudrate=9600)

# known prefixes
types = {'6F': 'Card','28':'Fob'}
goodcards = {}

# list of valid cards
with open('/home/pi/known_cards.csv') as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		cardhex, person = row
		goodcards[cardhex] = person

print goodcards
code = ''

def unlock_door():
	#os.system ("aplay -q /opt/sounds/granted.wav")
	GPIO.output(21, True)
	time.sleep(3)
	GPIO.output(21, False)

while True:
	data = serial.read()
	input_state = GPIO.input(13)
	if data == '\r':
		card = code[-12:-2]
		prefix = card[0:2]
		cardno = card[2:10]
		#print(card,types[prefix],int(cardno,16))
		cardstr = card,types[prefix],int(cardno,16)
		print cardstr
		code = ''
		if goodcards.has_key(card):
			syslog.syslog('ALLOWED ' + str(cardstr))
			print "ALLOWED: " + goodcards[card]
			os.system ("mpg123 -q /opt/sounds/granted.mp3 &")
			unlock_door()
		else:
			syslog.syslog('DENIED ' + str(cardstr))
			print "DENIED - unknown card"
			os.system ("mpg123 -q /opt/sounds/denied.mp3 &")
	else:
		code = code + data
