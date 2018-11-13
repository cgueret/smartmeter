'''
Created on 8 Nov 2018

@author: christophe.gueret
'''
from flask import Flask, render_template
app = Flask(__name__)

import pymysql
from datetime import datetime, date, timedelta

# select datetime, sum(revs) from readings group by day(datetime), hour(datetime), floor(minute(datetime) / 30);

# DB parameters
DB_PARAMS = {
	'user': 'pi',
	'host': 'localhost',
	'password': 'pi',
	'unix_socket': '/tmp/mysql.sock',
	'cursorclass': pymysql.cursors.DictCursor,
	'database': 'smartmeter',
	'charset': 'utf8'
}

DELTA = 1

def get_labels():
	labels = []
	t = datetime(hour=0, minute=0, year=1970, day=1, month=1)
	while (t.day != 2):
		labels.append(datetime.strftime(t, "%H:%M"))
		t = t + timedelta(minutes=DELTA)
	return labels

def get_day(db, day, month, year):
	buffer = {}
	total = 0
	with db.cursor() as cursor:
		try:
			query = """
			select datetime as ts, revs as r from readings 
			where day(datetime)={} and month(datetime)={} and year(datetime)={}
			""".format(day, month, year)
			print (query)
			cursor.execute(query);
			for row in cursor.fetchall():
				total = total + int(row['r'])
				dt = datetime.strftime(row['ts'], "%H:%M")
				buffer[dt] = total
		except Exception as e:
			print (e)
	return buffer
	
@app.route('/api/speed')
def api_speed():
	speed = 0
	db = pymysql.connect(**DB_PARAMS)
	with db.cursor() as cursor:
		try:
			cursor.execute("SELECT value FROM smartmeter.status WHERE parameter='current_speed'");
			for row in cursor.fetchall():
				speed = round(float(row['value']), 2)
		except Exception as e:
			print (e)
	db.close()
	return 'data\n{}'.format(speed)

@app.route('/api/histogram')
def api_histogram():
	# Get data
	db = pymysql.connect(**DB_PARAMS)
	today = date.today()
	yesterday = today - timedelta(days=1)
	yesterday_data = get_day(db, yesterday.day, yesterday.month, yesterday.year)
	today_data = get_day(db, today.day, today.month, today.year)
	db.close()
	buffer = "x,yesterday,today\n"
	last_seen_yesterday = 0
	last_seen_today = 0
	for l in get_labels():
		yesterday_p = last_seen_yesterday
		if l in yesterday_data:
			yesterday_p = yesterday_data[l]
			last_seen_yesterday = yesterday_p
		today_p = last_seen_today
		if l in today_data:
			today_p = today_data[l]
			last_seen_today = today_p
			
		buffer += "1970-01-01 {}:00,{},{}\n".format(l, yesterday_p, today_p)
	return buffer

@app.route('/')
def home():
	return render_template('index.html', title='Smart meter', labels = get_labels())

if __name__ == '__main__':
	app.jinja_env.auto_reload = True
	app.config['TEMPLATES_AUTO_RELOAD'] = True
	app.run(host='0.0.0.0', port=8080)
