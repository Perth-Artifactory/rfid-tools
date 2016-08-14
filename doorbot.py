#!/usr/bin/env python
from time import gmtime, strftime
import urllib2
import time
import RPi.GPIO as GPIO
import csv
import os
import syslog
import json
import socket

## Where do we store the access cards
cardfile = '/home/pi/known_cards.csv'


# merged in irker client to notify the IRC channel when door opened
irker_server = ("core", 6659)
target = "ircs://chat.freenode.net/artifactory"
subsystem = 'Doorbot: '
curtime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
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
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(21, GPIO.OUT) # Relay 1

import serial
serial = serial.Serial("/dev/ttyAMA0", baudrate=9600)

types = {'6F': 'Card','28':'Fob','1D':'Card', '1C':'Card'}
knowncards = {}

# list of valid cards
with open(cardfile) as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        cardhex, person, disabled = row
        knowncards[cardhex] = [person,bool(disabled)]
print knowncards
irk('Started - %d cards loaded' % len(knowncards))

code = ''

def unlock_door():
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
                if prefix in types:
                        tagtype = types[prefix]
                else:
                        tagtype = 'RFID'
                cardstr = card,tagtype,int(cardno,16)
                print cardstr
                code = ''
                if knowncards.has_key(card):
                        print "KNOWN %s %s presented at door" % (cardstr[1],cardstr[2])
                        # Has card been disabled?
                        if knowncards[card][1]:
                                print "DISABLED: " + knowncards[card][0]
                                os.system ("mpg123 -q /opt/sounds/denied.mp3 &")
                                syslog.syslog('DENIED: %s (Card Disabled) %s' % (knowncards[card][0],int(cardno,16)))
                                irk('\x1b[31m'+knowncards[card][0] +'\x1b[0m denied access')
                        else:
                                if (knowncards[card][0] == ''):
                                        print "ALLOWED UNMAPPED USER"
                                        syslog.syslog('ALLOWED: UNMAPPED USER %s' % int(cardno,16))
                                        irk('\x1b[33mUnknown User\x1b[0m opened the door')
                                else:
                                        print "ALLOWED: " + knowncards[card][0]
                                        syslog.syslog('ALLOWED: %s %s' % (knowncards[card][0],int(cardno,16)))
                                        irk('\x1b[32m' + knowncards[card][0]+ 'opened the door')
                                        cmd="curl -g http://10.60.210.69/entryapi.php?entryname='%s'?time='%s'" % (knowncards[card][0],curtime)
                                        os.system(cmd)
                                os.system ("mpg123 -q /opt/sounds/granted.mp3 &")
                                unlock_door()
                else:
                        print "UNKNOWN Card/Fob"
                        syslog.syslog('DENIED ' + str(cardstr))
                        os.system ("mpg123 -q /opt/sounds/denied.mp3 &")
                        irk('\x1b[31mUnknown Card\x1b[0m presented at door')
        else:
                code = code + data

# unlikely to get here...
