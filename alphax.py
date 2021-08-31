import websocket
import _thread
import time
import json
import pandas as pd
import talib
from talib.abstract import *
from talib import MA_Type
from csv import writer
from datetime import datetime
import pytz
from binance import ThreadedWebsocketManager


class AlphaX:
    # init
    _asset_free_balance = 0.0
    _asset_locked_balance = 0.0
    _asset_name = None
    _asset_pair = None
    _asset_df = None
    _kline_interval = None
    _previous_signal = 0
    _current_signal = 0
    _trigger = False
    _long_timeperiod = 0
    _short_timeperiod = 0
    _timezone = None
    _ledger_dict = {}

    def __init__(self):
        self._timezone = pytz.timezone('Asia/Kolkata')

    def _adj_column_names(self, dataframe):
        """
        ta-lib expects columns to be lower case; to be consistent,
        change date index
        """
        ts = dataframe
        ts.columns = [col.lower().replace(' ', '_') for col in ts.columns]
        ts.index.names = ['date']
        return ts

    def _write_to_csv(self, data, file_name):
        with open(file_name, 'a') as f_object:
            writer_object = writer(f_object)
            writer_object.writerow(data)
            f_object.close()

    def run_kline_websocket(self):
        def ws_message(ws, message):
            print("WebSocket thread: %s" % message)
            json_object = json.loads(message)
            kline_timestamp = json_object["k"]["t"]

        def ws_open(ws):
            ws.send('{"method": "LIST_SUBSCRIPTIONS", "id": 3}')

        def ws_thread(*args):
            ws_link = "wss://stream.binance.com:9443/ws/" + \
                      self._asset_pair.lower() + "@kline_" + self._kline_interval
            ws = websocket.WebSocketApp(
                ws_link, on_open=ws_open, on_message=ws_message)
            ws.run_forever()

        _thread.start_new_thread(ws_thread, ())

    def set_asset_name(self, asset_name):
        self._asset_name = str(asset_name)

    def set_timeperiods(self, long_tp, short_tp):
        self._long_timeperiod = int(long_tp)
        self._short_timeperiod = int(short_tp)

    def set_asset_pair(self, asset_pair):
        self._asset_pair = str(asset_pair)

    def set_kline_interval(self, kline_interval):
        self._kline_interval = kline_interval

    def set_asset_balance(self, client):
        self._asset_balance = client.get_asset_balance(asset=self._asset_name)
        self._asset_free_balance = float(self._asset_balance.get('free'))
        self._asset_locked_balance = float(self._asset_balance.get('locked'))

    def get_asset_balance(self):
        print("Asset: " + self._asset_balance.get('asset'))
        print("Asset balance [free]: %5.5f" % self._asset_free_balance)
        print("Asset balance [locked]: %5.5f" % self._asset_locked_balance)

    def get_timestamp_unixtime(self):
        """
        @returns Unix timestamp of one day before the current time
        @formula: current_time - time_interval_of_one_day -> this formula returns without milliseconds
        NOTE: binance API requires time with milliseconds. therefore we multiply with 1000
        """
        current_time = int(time.time())
        number_of_hours = 125
        one_hour_interval = 3600
        timestamp = (current_time - (number_of_hours *
                                     one_hour_interval)) * 1000
        return timestamp

    def dump_asset_kline_history(self, client):
        timestamp = self.get_timestamp_unixtime()
        bars = client.get_historical_klines(
            self._asset_pair, self._kline_interval, timestamp, limit=1000)

        for line in bars:
            del line[5:]

        self._asset_df = pd.DataFrame(
            bars, columns=['date', 'open', 'high', 'low', 'close'])
        self._asset_df.set_index('date', inplace=True)

    def calculate_ema(self, client, _asset_ledger=None):
        ts = self._adj_column_names(self._asset_df)
        ema_long = EMA(ts, timeperiod=self._long_timeperiod)
        ema_short = EMA(ts, timeperiod=self._short_timeperiod)

        ema_long_adjusted = pd.DataFrame(ema_long, columns=['ema']).iat[-1, 0]
        ema_short_adjusted = pd.DataFrame(
            ema_short, columns=['ema']).iat[-1, 0]

        # trigger logic
        self._current_signal = 1 if ema_long_adjusted < ema_short_adjusted else 0
        self._trigger = True if (self._current_signal != self._previous_signal) else False

        self._ledger_dict = {
                "time": datetime.now(self._timezone).strftime("%Y-%m-%d %H:%M:%S.%f"),
                "ema_long": ema_long_adjusted,
                "ema_short": ema_short_adjusted,
                "current_signal": self._current_signal,
                "previous_signal": self._previous_signal,
                "trigger": self._trigger,
                "current_asset_price": self.get_current_asset_price(client)
        }

        # print(self._ledger_dict)
        
        if self._trigger is True:
            _asset_ledger.append(self._ledger_dict)

        # --------------------Can be commented out---------------------
        # List = [datetime.now(self._timezone).strftime("%Y-%m-%d %H:%M:%S.%f"), ema_long_adjusted, ema_short_adjusted,
        #         self._current_signal, self._previous_signal, self._trigger, self.get_current_asset_price(client)]
        # self._write_to_csv(List, "btc_25_7.csv")
        # -------------------------------------------------------------

        self._previous_signal = self._current_signal

    def get_current_asset_price(self, client):
        asset_price = client.get_symbol_ticker(symbol=self._asset_pair)
        return float(asset_price["price"])

    def buy_sell_signal(self):
        pass
        # when trigger is true
        # if current_signal is 1, then buy
        # else sell

        # replace "create_test_order" with "create_order"
        # buy_order_limit = client.create_test_order(
        #     symbol='ETHUSDT',
        #     side='BUY',
        #     type='LIMIT',
        #     timeInForce='GTC',
        #     quantity=100,
        #     price=200)

    def run(self, client, _asset_ledger):
        self.set_asset_pair("BTCUSDT")
        self.set_kline_interval("15m")
        self.set_timeperiods(25, 7)
        self.dump_asset_kline_history(client)
        self.calculate_ema(client, _asset_ledger)

