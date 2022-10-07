FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN curl -sS https://downloads.mariadb.com/MariaDB/mariadb_repo_setup | bash
RUN apt update
RUN apt install libmariadb3 -y
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]