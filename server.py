'''
Created on 8 Nov 2018

@author: christophe.gueret
'''
import random
from flask import Flask, render_template
app = Flask(__name__)

# select datetime, sum(revs) from readings group by day(datetime), hour(datetime), floor(minute(datetime) / 30);

@app.route('/api/speed')
def api_speed():
	return 'data\n{}'.format(round(random.random()*100, 2))

@app.route('/')
def home():
	return render_template('index.html', title='Smart meter')

if __name__ == '__main__':
	app.jinja_env.auto_reload = True
	app.config['TEMPLATES_AUTO_RELOAD'] = True
	app.run(host='0.0.0.0', port=8080)
