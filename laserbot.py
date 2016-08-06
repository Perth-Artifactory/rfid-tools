#!/usr/bin/env python
import subprocess
import time
import RPi.GPIO as GPIO
import csv
import os
import syslog
import json
import socket
from datetime import timedelta

## Where do we store the access cards
cardfile = '/home/pi/known_cards.csv'

# merged in irker client to notify the IRC channel when door opened
irker_server = ("core", 6659)
target = "ircs://chat.freenode.net/artifactory"
subsystem = 'Laserbot: '
loggedon = ''
def connect():
    return socket.create_connection(irker_server)

def send(s, target, message):
    data = {"to": target, "privmsg" : message}
    dump = json.dumps(data)
    if not isinstance(dump, bytes):
        dump = dump.encode('ascii')
    s.sendall(dump)

def irk(message):
    try:
        s = connect()
        send(s, target, subsystem + message)
        s.close()
    except socket.error as e:
        sys.stderr.write("irk: write to server failed: %r\n" % e)

##########

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(23, GPIO.OUT) # Relay 1
GPIO.output(23, False)
GPIO.setup(16, GPIO.OUT) # RED LED
GPIO.setup(21, GPIO.OUT) # ORANGE LED
GPIO.setup(20, GPIO.OUT) # GREEN LED
GPIO.output(21, False)
GPIO.output(16, True)
GPIO.output(20, False)
GPIO.output(20, False)
irk('BigRed RFID doorbot.py Started')

import serial
serial = serial.Serial("/dev/ttyAMA0", baudrate=9600)

types = {'6F': 'Card','28':'Fob'}
knowncards = {}

# list of valid cards
with open(cardfile) as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        cardhex, person, disabled = row
        knowncards[cardhex] = [person,bool(disabled)]
print knowncards

code = ''

def unlock_bigred():
	GPIO.output(23, True)
	time.sleep(3)
	GPIO.output(23, False)




while True:
	data = serial.read()
	input_state = GPIO.input(23)
	if data == '\r':
		card = code[-12:-2]
		prefix = card[0:2]
		cardno = card[2:10]
		cardstr = card,types[prefix],int(cardno,16)
		print cardstr
		code = ''
		if knowncards.has_key(card):
			print "KNOWN %s %s presented at laser" % (cardstr[1],cardstr[2])
			# Has card been disabled?
			if knowncards[card][1]:
				print "DISABLED: " + knowncards[card][0]
				syslog.syslog('DENIED: %s (Card Disabled) %s' % (knowncards[card][0],int(cardno,16)))
				GPIO.output(16, False) #Red
				GPIO.output(20, False) #Green
				#Flash orange to show denied
				time.sleep(0.5)
				GPIO.output(21, True) #Orange
				time.sleep(0.5)
				GPIO.output(21, False) #Orange
				time.sleep(0.5)
				GPIO.output(21, True) #Orange
				time.sleep(0.5)
				GPIO.output(21, False) #Orange
				time.sleep(0.5)
				GPIO.output(21, True) #Orange
				time.sleep(0.5)
				GPIO.output(21, False) #Orange
				time.sleep(0.5)
				GPIO.output(21, True) #Orange
				time.sleep(0.5)
				GPIO.output(21, False) #Orange
				GPIO.output(16, True) #Red

				irk('\x1b[31m'+knowncards[card][0] +'\x1b[0m denied access')
			else:
				if (knowncards[card][0] == ''):
					print "DENIED UNMAPPED USER"
					syslog.syslog('DENIED: UNMAPPED USER %s' % int(cardno,16))
					irk('\x1b[33mUnknown User\x1b[0m DENIED on BigRed')
					GPIO.output(16, False) #Red
					GPIO.output(20, False) #Green
					#Flash orange to show denied
					time.sleep(0.5)
					GPIO.output(21, True) #Orange
					time.sleep(0.5)
					GPIO.output(21, False) #Orange
					time.sleep(0.5)
					GPIO.output(21, True) #Orange
					time.sleep(0.5)
					GPIO.output(21, False) #Orange
					time.sleep(0.5)
					GPIO.output(21, True) #Orange
					time.sleep(0.5)
					GPIO.output(21, False) #Orange
					time.sleep(0.5)
					GPIO.output(21, True) #Orange
					time.sleep(0.5)
					GPIO.output(21, False) #Orange
					GPIO.output(16, True) #Red


				else:
					print "ALLOWED: " + knowncards[card][0]



				if loggedon == '':
					syslog.syslog('ALLOWED: %s %s' % (knowncards[card][0],int(cardno,16)))
					irk('\x1b[32m' + knowncards[card][0]+ '\x1b[0m Logged On - BigRed')
					loggedon = 1
					start = time.clock()
					userlogged = '%s'
					GPIO.output(16, False) #Red
					GPIO.output(20, True) #Green
					unlock_bigred()
					continue

				if loggedon:
					irk('\x1b[32m' + knowncards[card][0]+ '\x1b[0m Logged off BigRed - Total Machine/Laser Time:')
					loggedon = ''
					elapsed = (time.clock() - start)
					outstr = str(elapsed / 10)
					GPIO.output(16, True) #Red
					GPIO.output(20, False) #Green

					irk(outstr)

					start = ''
					elapsed = ''
					outstr = ''

		else:
			print "UNKNOWN Card/Fob"
			syslog.syslog('DENIED ' + str(cardstr))
			os.system ("mpg123 -q /opt/sounds/denied.mp3 &")
			irk('\x1b[31mUnknown Card\x1b[0m presented at BigRed')
			GPIO.output(16, False) #Red
			GPIO.output(20, False) #Green
			#Flash orange to show denied
			time.sleep(0.5)
			GPIO.output(21, True) #Orange
			time.sleep(0.5)
			GPIO.output(21, False) #Orange
			time.sleep(0.5)
			GPIO.output(21, True) #Orange
			time.sleep(0.5)
			GPIO.output(21, False) #Orange
			time.sleep(0.5)
			GPIO.output(21, True) #Orange
			time.sleep(0.5)
			GPIO.output(21, False) #Orange
			time.sleep(0.5)
			GPIO.output(21, True) #Orange
			time.sleep(0.5)
			GPIO.output(21, False) #Orange
			GPIO.output(16, True) #Red

	else:
		code = code + data

# unlikely to get here...
