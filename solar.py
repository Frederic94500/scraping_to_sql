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
            soup = Bs(requests.get(self.ADDRESS, timeout=10,
                                   auth=(self.CFG["SOLAR"]["user"], self.CFG["SOLAR"]["password"])).content, "lxml")
            escapes = ''.join([chr(char) for char in range(1, 32)])
            soup.find_all('script')[1].text.translate(str.maketrans('', '', escapes))
            data = soup.find_all('script')[1].text.translate(str.maketrans('', '', escapes)) \
                .replace("\"", "") \
                .replace("var", "") \
                .replace(" ", "") \
                .split(";")
            output = data[5:8]
            return float(output[0].split("=")[1]), float(output[1].split("=")[1]), float(output[2].split("=")[1])
        except (ConnectionError, requests.exceptions.ConnectionError, socket.error, socket.gaierror,
                socket.herror, socket.timeout):
            raise ConnectionError()
        except ValueError:
            raise ValueError()

    def commit_entry_instant_inverter_power(self, cursor, timestamp, power):
        temp_inverter_instant = self.INVERTER_NO + "_instant"
        cursor.execute(f"INSERT INTO {temp_inverter_instant} (timestamp, power) VALUES (?,?)", (timestamp, power))
        print(timestamp + " - " + self.INVERTER_NO + " - Instant committed")

    def commit_entry_total_inverter(self, cursor, timestamp, total):
        temp_inverter_total = self.INVERTER_NO + "_total"
        cursor.execute(f"SELECT power FROM {temp_inverter_total} ORDER BY timestamp DESC LIMIT 1;")
        print(timestamp + " - " + self.INVERTER_NO + " - Total asked")
        (temp_total,) = cursor.fetchone()

        if temp_total < total:
            cursor.execute(f"INSERT INTO {temp_inverter_total} (timestamp, power) VALUES (?,?)", (timestamp, total))
            print(timestamp + " - " + self.INVERTER_NO + " - Total committed")

    def get_information(self, cursor, timestamp):
        instant_inverter_power, temp_daily, temp_total = 0, 0, 0
        try:
            self.latest_power, temp_daily, temp_total = self.scraper()
            instant_inverter_power = self.latest_power
            self.commit_entry_total_inverter(cursor, timestamp, temp_total)
        except (ConnectionError, ValueError):
            if 4 <= int(datetime.now(timezone.utc).strftime('%H')) < 20:
                instant_inverter_power = self.latest_power
            else:
                instant_inverter_power, self.latest_power = 0, 0
        finally:
            self.commit_entry_instant_inverter_power(cursor, timestamp, instant_inverter_power)
            return self.latest_power, temp_daily, temp_total
