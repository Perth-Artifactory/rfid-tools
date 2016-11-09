#!/usr/bin/env python
import sys
from time import gmtime, strftime
import time
import csv
import os
import syslog
import json
import socket

## Where do we store the access cards
cardfile = 'known_cards.csv'


# merged in irker client to notify the IRC channel when door opened
irker_server = ('core', 6659)
target = 'ircs://chat.freenode.net/artifactory'
subsystem = 'Doorbot: '
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

import serial
serial = serial.Serial("/dev/ttyACM0", baudrate=9600)
#serial = serial.Serial("/dev/tty.wchusbserial1410", baudrate=9600, timeout=0)

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
syslog.syslog('Doorbot started')

code = ''
data = ''

def unlock_door():
    serial.write('A')
    time.sleep(3)
    serial.write('a')

while True:
  try:
    while serial.inWaiting() > 0:
      data = serial.readline()
      print data
      if "RFID" in data:
        card = data[-11:-1]
        print card
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
                os.system ("mpg123 -q /home/pi/denied.mp3 &")
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
                    irk('\x1b[32m' + knowncards[card][0]+ '\x1b[0m opened the door')
                    #cmd="curl -g http://10.60.210.69/entryapi.php?entryname='%s'?time='%s'" % (knowncards[card][0],curtime)
                    #os.system(cmd)
                os.system ("mpg123 -q /home/pi/granted.mp3 &")
                unlock_door()
        else:
            print "UNKNOWN Card/Fob"
            syslog.syslog('DENIED ' + str(cardstr))
            os.system ("mpg123 -q /home/pi/denied.mp3 &")
            irk('\x1b[31mUnknown Card\x1b[0m presented at door')
    else:
        code = code + data
  except (SystemExit, KeyboardInterrupt):
    irk('Shutting Down')
    syslog.syslog('Doorbot shutting down')
    break
