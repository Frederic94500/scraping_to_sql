FROM python:slim

WORKDIR /usr/src/app

RUN apt update && apt install -y curl && curl -sS https://downloads.mariadb.com/MariaDB/mariadb_repo_setup | bash && apt update && apt install libmariadb3 libmariadb-dev gcc -y && apt clean

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./main.py" ]