import sys
import time
from configparser import ConfigParser
from datetime import timezone, datetime

import mariadb as mariadb
import requests

from solar import Solar


def get_sunrise_sunset(lat, lng):
    data = requests.get(f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lng}&formatted=0").json()
    return datetime.fromisoformat(data["results"]["sunrise"]), datetime.fromisoformat(data["results"]["sunset"])


if __name__ == '__main__':
    cfg = ConfigParser()
    cfg.read(".log.cfg")

    try:
        connection = mariadb.connect(
            host=cfg["MARIADB"]["host"],
            port=int(cfg["MARIADB"]["port"]),
            user=cfg["MARIADB"]["user"],
            password=cfg["MARIADB"]["password"],
            database=cfg["MARIADB"]["database"]
        )
        connection.autocommit = True
        connection.auto_reconnect = True
        cursor = connection.cursor()
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    inverters = [
        Solar("4135604662", "http://192.168.50.62/status.html", cfg),
        Solar("4112820780", "http://192.168.50.80/status.html", cfg),
        Solar("4113425594", "http://192.168.50.94/status.html", cfg)
    ]

    cursor.execute("SELECT power FROM total ORDER BY timestamp DESC LIMIT 1;")
    (max_total,) = cursor.fetchone()

    sunrise, sunset = get_sunrise_sunset(cfg["COORDS"]["lat"], cfg["COORDS"]["lng"])
    max_daily = 0

    while connection.open:
        instant, daily, total = 0, 0, 0
        if sunrise <= datetime.now(timezone.utc) <= sunset:
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            for inverter in inverters:
                instant_inv, daily_inv, total_inv = inverter.get_information(cursor, timestamp)
                instant += instant_inv
                daily += daily_inv
                total += total_inv
            if instant > 0:
                cursor.execute("INSERT INTO instant (timestamp, power) VALUES (?,?)", (timestamp, instant))
            if daily != 0 and daily >= max_daily:
                max_daily = daily
                cursor.execute("INSERT INTO daily (timestamp, power) VALUES (?,?)", (timestamp, daily))
            if total != 0 and total >= max_total:
                max_total = total
                cursor.execute("INSERT INTO total (timestamp, power) VALUES (?,?)", (timestamp, total))
            time.sleep(30)
        else:
            time.sleep(600)
            sunrise, sunset = get_sunrise_sunset(cfg["COORDS"]["lat"], cfg["COORDS"]["lng"])
            max_daily = 0

    cursor.close()
    connection.close()
    sys.exit(0)
