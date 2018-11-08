#!/usr/bin/env python
import time
import datetime

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
VERSION = 1.1

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
	elif version == '1.0':
	    cursor.execute("CREATE TABLE smartmeter.readings (datetime DATETIME NOT NULL, revs INT NOT NULL, PRIMARY KEY (datetime) ) CHARSET=utf8;")
	    cursor.execute("UPDATE smartmeter.status SET value='1.1' WHERE parameter='version'")
	    db.commit()
    db.close()

def loop():
    b = 0
    start = time.time()
    revs = 0

    # Get the last time we recorded a number of revolutions
    last_reading = None
    db = pymysql.connect(**DB_PARAMS)
    with db.cursor() as cursor:
	cursor.execute("SELECT datetime FROM smartmeter.readings ORDER BY datetime DESC LIMIT 1")
	for row in cursor.fetchall():
	    last_reading = row['datetime']
    print ('Last reading: {}'.format(last_reading))

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

		# See if we need to record a new reading
		spacing = 60 # 1 minute
		rounded_time = datetime.datetime.fromtimestamp(round(time.time() / spacing, 0) * spacing)
		if rounded_time != last_reading:
		    print ('{} => {}'.format(rounded_time, revs))
		    db = pymysql.connect(**DB_PARAMS)
		    try:
			with db.cursor() as cursor:
			    cursor.execute("INSERT INTO smartmeter.readings VALUES('{}', '{}')".format(rounded_time.strftime('%Y-%m-%d %H:%M:%S'), revs))
			db.commit()
		    finally:
			db.close()
		    last_reading = rounded_time
		    revs = 0

def destroy():
    GPIO.cleanup()

if __name__ == '__main__':
    setup()
    initdb()
    try:
	loop()
    except KeyboardInterrupt:
	destroy()

#ts = time.time()
#st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
