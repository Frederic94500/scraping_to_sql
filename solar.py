import socket
from configparser import ConfigParser
from datetime import timezone, datetime

import requests
from bs4 import BeautifulSoup as Bs


class Solar:
    INVERTER_NO = ""
    ADDRESS = ""
    CFG = ConfigParser()
    latest_power = 0

    def __init__(self, inverter_no, address, cfg):
        self.INVERTER_NO = inverter_no
        self.ADDRESS = address
        self.CFG = cfg

    def scraper(self):
        try:  # Password here
            soup = Bs(requests.get(self.ADDRESS, timeout=10, auth=(self.CFG["SOLAR"]["user"], self.CFG["SOLAR"]["password"])).content, "lxml")
            data = soup.find_all('script')[1].text.strip().split(";")
            return data
        except (ConnectionError, requests.exceptions.ConnectionError, socket.error, socket.gaierror,
                socket.herror, socket.timeout):
            raise ConnectionError()

    def commit_entry_instant_inverter_power(self, cursor, timestamp, power):
        temp_inverter_instant = self.INVERTER_NO + "_instant"
        cursor.execute(f"INSERT INTO {temp_inverter_instant} (timestamp, power) VALUES (?,?)", (timestamp, power))
        print(timestamp + " - " + self.INVERTER_NO + " - Instant committed")

    def commit_entry_total_inverter(self, cursor, timestamp, total):
        temp_inverter_total = self.INVERTER_NO + "_total"
        cursor.execute(f"SELECT power FROM {temp_inverter_total} ORDER BY timestamp DESC LIMIT 1;")
        print(timestamp + " - " + self.INVERTER_NO + " - Total asked")
        (temp_total, ) = cursor.fetchone()

        if temp_total < total:
            cursor.execute(f"INSERT INTO {temp_inverter_total} (timestamp, power) VALUES (?,?)", (timestamp, total))
            print(timestamp + " - " + self.INVERTER_NO + " - Total committed")

    def get_information(self, cursor, timestamp):
        instant_inverter_power, temp_daily, temp_total = 0, 0, 0
        try:
            data = self.scraper()
            self.latest_power = int(data[5][23:-1])
            instant_inverter_power = int(data[5][23:-1])
            temp_daily = float(data[6][25:-1])
            temp_total = float(data[7][25:-1])
            self.commit_entry_total_inverter(cursor, timestamp, temp_total)
        except (ConnectionError, ValueError):
            if 4 <= int(datetime.now(timezone.utc).strftime('%H')) < 20:
                instant_inverter_power = self.latest_power
            else:
                instant_inverter_power, self.latest_power = 0, 0
        finally:
            self.commit_entry_instant_inverter_power(cursor, timestamp, instant_inverter_power)
            return self.latest_power, temp_daily, temp_total
