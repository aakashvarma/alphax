from flask import Flask
from alphax import AlphaX

import os
from binance.client import Client
from apscheduler.schedulers.background import BackgroundScheduler

api_key = os.environ.get('binance_api')
api_secret = os.environ.get('binance_secret')

client = Client(api_key, api_secret)
client.API_URL = 'https://api.binance.com/api'

bot = AlphaX()
bot1 = AlphaX()

def execute():
    bot.run(client, "BTCUSDT", "15m", 50, 14)
    bot1.run(client, "BTCUSDT", "1h", 50, 14)


sched = BackgroundScheduler(daemon=True)
sched.add_job(execute, 'interval', minutes=1)
sched.start()


# __________ flask app _____________

app = Flask(__name__)


@app.route("/")
def index():
    return "welcome to the future. -AlphaX"


if __name__ == "__main__":
    app.run()
