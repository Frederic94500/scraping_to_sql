import socket
from datetime import timezone, datetime

import requests
from bs4 import BeautifulSoup as Bs


class Solar:
    INVERTER_NO = ""
    ADDRESS = ""
    latest_power = 0

    def __init__(self, inverter_no, address):
        self.INVERTER_NO = inverter_no
        self.ADDRESS = address

    def scraper(self):
        try:
            soup = Bs(requests.get(self.ADDRESS, auth=("admin", "-")).content, "lxml")
            data = soup.find_all('script')[1].text.strip().split(";")
            return data
        except (ConnectionError, requests.exceptions.ConnectionError, socket.error, socket.gaierror,
                socket.herror, socket.timeout) as e:
            raise ConnectionError()

    def get_information(self, connection, cursor, timestamp):
        is_zero = False
        instant_inverter_power = 0
        temp_daily = 0
        temp_total = 0
        try:
            data = self.scraper()
            self.latest_power = int(data[5][23:-1])
            instant_inverter_power = int(data[5][23:-1])
            temp_daily = float(data[6][25:-1])
            temp_total = float(data[7][25:-1])
            self.commit_entry_total_inverter(connection, cursor, timestamp, temp_total)
        except (ConnectionError, ValueError) as e:
            if 4 <= int(datetime.now(timezone.utc).strftime('%H')) < 20:
                is_zero = False
            else:
                print(e)
                instant_inverter_power = 0
                is_zero = True
        finally:
            self.commit_entry_instant_inverter_power(connection, cursor, timestamp, instant_inverter_power)
            return is_zero, self.latest_power, temp_daily, temp_total

    def commit_entry_instant_inverter_power(self, connection, cursor, timestamp, power):
        temp_inverter_instant = self.INVERTER_NO + "_inst"
        cursor.execute(f"INSERT INTO {temp_inverter_instant} (timestamp, power) VALUES (?,?)", (timestamp, power))
        connection.commit()

    def commit_entry_total_inverter(self, connection, cursor, timestamp, total):
        temp_inverter_total = self.INVERTER_NO + "_total"
        temp_total = 0.0
        cursor.execute(f"SELECT power FROM {temp_inverter_total} ORDER BY timestamp DESC LIMIT 1;")
        for (total_c,) in cursor:
            temp_total = total_c
        if temp_total < total:
            cursor.execute(f"INSERT INTO {temp_inverter_total} (timestamp, power) VALUES (?,?)", (timestamp, total))
            connection.commit()
