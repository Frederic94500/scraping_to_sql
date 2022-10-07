import socket
import sys
import time
from datetime import timezone, datetime

import mariadb as mariadb
import requests
from bs4 import BeautifulSoup as Bs

if __name__ == '__main__':
    try:
        connection = mariadb.connect(
            host="192.168.50.227",
            port=3306,
            user="root",
            password="-",
            database="solar"
        )
        cursor = connection.cursor()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    inverters = [
        {"inverter_no": "4135604662", "address": "http://192.168.50.62/status.html", "previous": 0},
        {"inverter_no": "4112820780", "address": "http://192.168.50.80/status.html", "previous": 0},
        {"inverter_no": "4113425594", "address": "http://192.168.50.94/status.html", "previous": 0}
    ]

    counter_zero = 0
    max_daily = 0
    max_total = 0
    reset = 0
    while True:
        inst = 0
        daily = 0
        total = 0
        if counter_zero < 6:
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            for inverter in inverters:
                inverter_p = 0
                try:
                    soup = Bs(requests.get(inverter["address"], auth=("admin", "-")).content, "lxml")
                    data = soup.find_all('script')[1].text.strip().split(";")
                    inverter_p = int(data[5][23:-1])
                    daily = daily + float(data[6][25:-1])
                    total = total + float(data[7][25:-1])
                    cursor.execute("INSERT INTO " + inverter["inverter_no"] + "_total (timestamp, power) VALUES (?,?)",
                                   (timestamp, float(data[7][25:-1])))
                    counter_zero = 0
                    inverter["previous"] = inverter_p
                except ValueError as e:
                    inverter_p = inverter["previous"]
                    counter_zero = 0
                except (ConnectionError, requests.exceptions.ConnectionError, socket.error, socket.gaierror,
                        socket.herror, socket.timeout) as e:
                    if 4 <= int(datetime.now(timezone.utc).strftime('%H')) < 20:
                        inverter_p = inverter["previous"]
                        counter_zero = 0
                    else:
                        print(e)
                        inverter_p = 0
                        counter_zero = counter_zero + 1
                finally:
                    inst = inst + inverter_p
                    cursor.execute("INSERT INTO " + inverter["inverter_no"] + "_inst (timestamp, power) VALUES (?,?)",
                                   (timestamp, inverter_p))
                    connection.commit()
            if inst > 0:
                cursor.execute("INSERT INTO inst (timestamp, power) VALUES (?,?)", (timestamp, inst))
            if daily != 0 and daily >= max_daily:
                max_daily = daily
                cursor.execute("INSERT INTO daily (timestamp, power) VALUES (?,?)", (timestamp, daily))
            if total != 0 and total >= max_total:
                max_total = total
                cursor.execute("INSERT INTO total (timestamp, power) VALUES (?,?)", (timestamp, total))
            connection.commit()
            time.sleep(30)
            reset = reset + 1
        elif reset >= 720:
            cursor.close()
            connection.close()
            sys.exit(0)
        else:
            time.sleep(600)
            max_daily = 0
            counter_zero = 0
            reset = reset + 20

