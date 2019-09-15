from flask import Flask, jsonify, request
from xecd_rates_client import XecdClient
import sqlite3
import base64
import string
import random

from dateutil.relativedelta import relativedelta
import datetime

account_id = 'xe891090202'
pwd = '8ht3qjhq8vnu0dbb91ai40p44b'
xecd = XecdClient(account_id, pwd)

db_name = 'database.db'


app = Flask(__name__)

# Getting column names
def dict_factory(cursor, row):
	d = {}
	for idx,col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d

def random_string(stringLength=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

# Save data to DB
@app.route('/api/data/save', methods=['POST'])
def save():
    data = request.get_json()
    b64 = data['b64']
    name = data['name']
    date = data['date']

    with sqlite3.connect(db_name) as conn:
        img_path = 'img/' + random_string() + '.jpg'

        imgdata = base64.b64decode(b64)
        with open(img_path, 'wb') as f:
            f.write(imgdata)

        cur = conn.cursor()
        cur.execute('INSERT INTO saved_data (img_path, name, date) VALUES (?, ?, ?)', (img_path, name, date))

    return jsonify('ok')

# Read data from DB
@app.route('/api/data', methods=['GET'])
def get_data():
    with sqlite3.connect(db_name) as conn:
        conn.row_factory = dict_factory
        cur = conn.cursor()
        cur.execute('SELECT * FROM saved_data')
        results = cur.fetchall()

    return jsonify(results)

# Get historical rates
@app.route('/api/history', methods=['GET'])
def history():
    currency_1 = request.args.get('c1')
    currency_2 = request.args.get('c2')

    todays_date = datetime.datetime.now()
    a_year_ago = str(todays_date - relativedelta(years=1))
    todays_date = str(todays_date)

    data = xecd.historic_rate_period(1, currency_1, currency_2, a_year_ago, todays_date, per_page=500)['to'][currency_2]

    return jsonify(data)

# Display all currencies
@app.route('/api/currencies', methods=['GET'])
def currencies():
    currencies = xecd.currencies()['currencies']
    processed_currencies = []
    for currency in currencies:
        short = currency['iso']
        long = currency['currency_name']
        symbol = None

        if(short == 'USD'):
            symbol = '$'
        elif(short == 'CAD'):
            symbol = '$'
        elif(short == 'GBP'):
            symbol = '£'
        elif(short == 'EUR'):
            symbol = '€'
        elif(short == 'INR'):
            symbol = '₹'
        
        processed_currencies.append({'short': short, 'long': long, 'symbol': symbol, 'flag': 'https://raw.githubusercontent.com/transferwise/currency-flags/master/src/flags/%s.png' % short.lower()})
        
    return jsonify(processed_currencies)

# Convert currencies
@app.route('/api/convert', methods=['GET'])
def convert():
    currency_1 = request.args.get('c1')
    currency_2 = request.args.get('c2')
    amount = request.args.get('a')
    response = xecd.convert_from(currency_1, currency_2, amount)
    return jsonify(response['to'][0]['mid'])


if __name__ == '__main__':
	app.run(host='0.0.0.0')