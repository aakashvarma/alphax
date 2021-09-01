from flask import Flask
from alphax import AlphaX

import os
from binance.client import Client
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

_asset_ledger = []

api_key = os.environ.get('binance_api')
api_secret = os.environ.get('binance_secret')

client = Client(api_key, api_secret)
client.API_URL = 'https://api.binance.com/api'

bot = AlphaX()

def execute():
    bot.run(client, _asset_ledger)

sched = BackgroundScheduler(daemon=True)
sched.add_job(execute, 'interval', minutes=60)
sched.start()


@app.route("/")
def index():
    return "welcome to the future. -AlphaX"


@app.route("/trigger_points/")
def get_data():
    return str(_asset_ledger)


if __name__ == "__main__":
    app.run()
