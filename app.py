from flask import Flask
from alphax import AlphaX
import socket
import time

import os
from binance.client import Client
from apscheduler.schedulers.background import BackgroundScheduler

api_key = os.environ.get('binance_api')
api_secret = os.environ.get('binance_secret')

client = Client(api_key, api_secret)
client.API_URL = 'https://api.binance.com/api'

bot = AlphaX()
bot1 = AlphaX()
bot2 = AlphaX()
bot3 = AlphaX()

def is_connected():
    try:
        socket.create_connection(("1.1.1.1", 53))
        return True
    except OSError:
        pass
    return False


def execute():
    if is_connected():
        bot.run(client, "BTCUSDT", "15m", 50, 14)
        bot1.run(client, "BTCUSDT", "15m", 25, 7)
        bot2.run(client, "BTCUSDT", "1h", 50, 14)
        bot3.run(client, "BTCUSDT", "1h", 25, 7)

    else:
        print(str(time.time()) + " - Internet not connected.")


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
