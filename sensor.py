#!/usr/bin/env python
import time

# TCRT5000 tracking sensor
# https://raspberrytips.nl/tcrt5000

import RPi.GPIO as GPIO
import pymysql

TrackingPin = 11
OutLedPin = 12

#  let roundedTime = (new Date(Math.round(now.getTime() / displayStatus.spacing) * displayStatus.spacing)).getTime();

# DB parameters
DB_PARAMS = {
    'host': 'localhost',
    'user': 'pi',
    'unix_socket': '/var/run/mysqld/mysqld.sock',
    'password': None,
    'cursorclass': pymysql.cursors.DictCursor,
    'charset': 'utf8'
}
VERSION = 1.0

def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(TrackingPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def initdb():
    db = pymysql.connect(**DB_PARAMS)
    with db.cursor() as cursor:
	version = None
	try:
	    cursor.execute("SELECT value FROM smartmeter.status WHERE parameter='version'");
	    for row in cursor.fetchall():
		version = row['value']
	except:
	    pass

	# Deal with the version
	if version == None:
	    cursor.execute("CREATE TABLE smartmeter.status (parameter VARCHAR(128) NOT NULL, value VARCHAR(128) NOT NULL, PRIMARY KEY (parameter) ) CHARSET=utf8;")
	    cursor.execute("INSERT INTO smartmeter.status VALUES ('version' , '1.0');")
	    cursor.execute("INSERT INTO smartmeter.status VALUES ('current_speed', '');")
	    db.commit()
    db.close()

def loop():
    b = 0
    start = time.time()
    revs = 0
    while True:
	if GPIO.input(TrackingPin) != GPIO.LOW:
	    # Red marker
	    b = b + 1
	else:
	    # Silver reflective part
	    if b > 1000:
		# We saw the red mark
		now = time.time()
		speed = now-start
		print ('Tick! {} {}'.format(b, speed))
		revs = revs + 1
		start = now
		b = 0
		
		# Update the speed tracker in the DB
		db = pymysql.connect(**DB_PARAMS)
		try:
		    query = "UPDATE smartmeter.status SET value='{}' WHERE parameter='current_speed'".format(speed)
		    with db.cursor() as cursor:
			cursor.execute(query)
		    db.commit()
		finally:
		    db.close()


def destroy():
    GPIO.cleanup()

if __name__ == '__main__':
    setup()
    initdb()
    try:
	loop()
    except KeyboardInterrupt:
	destroy()