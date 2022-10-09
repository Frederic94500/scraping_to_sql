FROM python:slim

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get install -y curl && \
    curl -sS https://downloads.mariadb.com/MariaDB/mariadb_repo_setup | bash && \
    apt-get update && \
    apt-get install libmariadb3 libmariadb-dev gcc -y && \
    apt-get clean

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]