import sys
import time
from datetime import timezone, datetime

import mariadb as mariadb

from solar import Solar

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
        Solar("4135604662", "http://192.168.50.62/status.html"),
        Solar("4112820780", "http://192.168.50.80/status.html"),
        Solar("4113425594", "http://192.168.50.94/status.html")
    ]

    cursor.execute("SELECT power FROM total ORDER BY timestamp DESC LIMIT 1;")
    max_total = 0
    for (total_c,) in cursor:
        max_total = total_c

    counter_zero, max_daily, reset = 0, 0, 0
    while True:
        instant, daily, total = 0, 0, 0
        if counter_zero < 6 and 4 <= int(datetime.now(timezone.utc).strftime('%H')) < 20:
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            for inverter in inverters:
                is_zero, instant_inv, daily_inv, total_inv = inverter.get_information(connection, cursor, timestamp)
                if is_zero:
                    counter_zero += 1
                else:
                    counter_zero = 0
                instant += instant_inv
                daily += daily_inv
                total += total_inv
            if instant > 0:
                cursor.execute("INSERT INTO inst (timestamp, power) VALUES (?,?)", (timestamp, instant))
            if daily != 0 and daily > max_daily:
                max_daily = daily
                cursor.execute("INSERT INTO daily (timestamp, power) VALUES (?,?)", (timestamp, daily))
            if total != 0 and total > max_total:
                max_total = total
                cursor.execute("INSERT INTO total (timestamp, power) VALUES (?,?)", (timestamp, total))
            connection.commit()
            time.sleep(30)
            reset += 30
        elif reset >= 7200:
            cursor.close()
            connection.close()
            sys.exit(0)
        else:
            time.sleep(600)
            max_daily, counter_zero = 0, 0
            reset += 600
